bl_info = {
    "name": "Growth Image",
    "description": "Generate a growth animation image based on an image.",
    "author": "Sebastian Staacks",
    "location": "Image Editor > Image > Generate growth data image",
    "wiki_url": "https://there.oughta.be/a/growth-image-blender-plugin",
    "blender": (2, 92, 0),
    "version": (1, 0),
    "category": "Animation",
}

import bpy
import math
from heapq import *

class GrowthImage(bpy.types.Operator):
    """Generate an image with sequence information to animate growing structures based on the currently selected image."""
    bl_idname = "image.generate_growth_image"
    bl_label = "Generate growth data image"
    bl_description = "This add on takes a loaded image (i.e. a texture) and generates a second image with non-color data that helps animating a growth of the original image. See https://there.oughta.be/a/growth-image-addon"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING'}
    
    origin: bpy.props.FloatVectorProperty(size=2, name="Origin", default=[0.5,0.5], min=0.0, max=1.0)
    radius: bpy.props.FloatProperty(name="Influence radius", default=1.5, min=1)
    channel: bpy.props.EnumProperty(items=[("r", "Red", "Red channel of source image is used as reference."), ("g", "Green", "Green channel of source image is used as reference."), ("b", "Blue", "Blue channel of source image is used as reference."), ("a", "Alpha", "Alpha channel of source image is used as reference.")], name="Reference channel", default=0)
    threshold: bpy.props.FloatProperty(name="Threshold", default=0.1, min=0.0, max=1.0)
    costabove: bpy.props.FloatProperty(name="Cost above threshold", default=1.0, min=0)
    costbelow: bpy.props.FloatProperty(name="Cost below threshold", default=1000000.0, min=0)
    timeabove: bpy.props.FloatProperty(name="Time above threshold", default=1.0, min=0)
    timebelow: bpy.props.FloatProperty(name="Time below threshold", default=2.0, min=0)
    
    def execute(self, context):
        self.cancelled = False
        wm = context.window_manager
        
        imageName = context.area.spaces.active.image.name
        if imageName[-7:] == "_growth":
            imageName = imageName[:-7]
        source = bpy.data.images[imageName]
        w, h = source.size

        threshold = self.threshold
        costabove = self.costabove
        costbelow = self.costbelow
        timeabove = self.timeabove
        timebelow = self.timebelow

        if self.channel == "r":
            channel = 0
        elif self.channel == "g":
            channel = 1
        elif self.channel == "b":
            channel = 2
        else:
            channel = 3
        origin = (int(min(w-1,max(0,w*self.origin[0]))), int(min(h-1,max(0,h*self.origin[1]))))
        radius = int(self.radius)

        print("Processing " + imageName + " with size " + str(w) + "x" + str(h))

        if imageName + "_growth" in bpy.data.images:
            target = bpy.data.images[imageName + "_growth"]
        else:
            target = bpy.data.images.new(imageName + "_growth", width=w, height=h, float_buffer=True, is_data=True)
        n = w*h*4
        t = list([-1.0] * n)
        s = source.pixels[:]

        todo = w*h
        progress = 0
        wm.progress_begin(0, todo)
        i = (origin[1]*w + origin[0])*4

        next = []
        heappush(next, (0, 0, 0, i))
        
        kernel = []
        for x in range(-radius, radius+1):
            for y in range(-radius, radius+1):
                if radius*radius < x*x+y*y:
                    continue
                kernel.append((4*x+4*y*w, math.sqrt(x*x+y*y)))

        while progress < todo:
            cost, distance, time, i = heappop(next)

            if t[i] >= 0:
                continue
            
            t[i] = cost
            t[i+1] = distance
            t[i+2] = time
            progress += 1
            if progress & 0x0fff == 0:
                wm.progress_update(progress)
                print("Progress: " + str(progress) + "/" + str(todo))
                
            for pixel in kernel:
                index = i+pixel[0]
                if index < 0 or index >= n:
                    continue
                if t[index] >= 0:
                    continue
                d = pixel[1]
                ncost = cost + d * (costabove if s[index+channel] > threshold else costbelow)
                ndistance = distance + d
                ntime = time + d * (timeabove if s[index+channel] > threshold else timebelow)
                heappush(next, (ncost, ndistance, ntime, index))


        print("Applying result...")
        target.pixels = t[:]
        target.update()
        #target.pack()
        wm.progress_end()
        print("Done.")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
def menu_func(self, context):
    self.layout.operator(GrowthImage.bl_idname)
        
def register():
    bpy.utils.register_class(GrowthImage)
    bpy.types.IMAGE_MT_image.append(menu_func)
    
def unregister():
    bpy.utils.unregister_class(GrowthImage)
        
if __name__ == "__main__":
    register()
