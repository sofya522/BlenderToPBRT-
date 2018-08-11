import bpy
import math
import os


scene = bpy.data.scenes["Scene"]
renderlayer = scene.render.layers["RenderLayer"]
userinput = "image.exr"
camera = bpy.data.cameras["Camera"]
env = "20060807_wells6_hd.exr"


path_to_location = "/Users/sneechie/desktop" 
blender_name =  bpy.path.basename(bpy.context.blend_data.filepath)[:-6]
directory =  "%s_pbrt" % blender_name
path_to_dir = "%s/%s/" % (path_to_location, directory)
output_path = "%s/%s/%s." % (path_to_location, directory, blender_name)
pbrtfilename = "%s.pbrt" % blender_name
use_obj = False; 

def create_directory(): 
	
	os.chdir("%s" % path_to_location)
	print("Exporting PBRT scene file to directory: %s\n" % directory)
	os.system ("mkdir %s" % directory)


create_directory()
pbrtfile = open('%spbrt' % output_path,'w')

def indent():
	pbrtfile.write('	')

def begin_attribute(): 
	pbrtfile.write("AttributeBegin\n")


def end_attribute(): 
	pbrtfile.write("AttributeEnd\n\n\n")

def get_integrator():
	integrator = scene.cycles.progressive
	if integrator == "PATH":
   		pbrtfile.write('Integrator \"path\" ')
	elif integrator == "BRANCHED_PATH":
		pbrtfile.write('Integrator \"bdpt\" ')
	maxdepth = scene.cycles.max_bounces
	pbrtfile.write('\"integer maxdepth\" [%d]\n' % maxdepth)

def get_sampler():
	sampler = scene.cycles.sampling_pattern 
	if sampler == "SOBOL":
		pbrtfile.write('Sampler \"sobol\"\n')
	spp = renderlayer.samples
	if spp == 0:
		spp = scene.cycles.samples
	indent()
	pbrtfile.write('\"integer pixelsamples\" [%d]\n' % spp)

def get_film():
	#pixel filter
	pbrtfile.write('PixelFilter ')
	pf_type = scene.cycles.pixel_filter_type
	
	if pf_type == "BOX" or pf_type == "BLACKMAN_HARRIS": 
		pbrtfile.write('\"box\"\n')
	elif pf_type == "GAUSSIAN": 
		pbrtfile.write('\"gaussian\"\n')

	filterwidth = scene.cycles.filter_width 
	indent()
	pbrtfile.write('\"float xwidth\" %f \"float ywidth\" %f\n' % (filterwidth, filterwidth))

	pbrtfile.write('Film \"image\" \"string filename\" [\"%s\"]\n' % userinput)

	res_x = scene.render.resolution_x
	res_y = scene.render.resolution_y
	indent()
	pbrtfile.write('\"integer xresolution\" [%d] \"integer yresolution\" [%d]\n\n' % (res_x, res_y)) 

def get_camera():

	pbrtfile.write("Scale -1 1 1\n")
	cam_context= bpy.context.scene.camera
	cam_context.rotation_mode = "AXIS_ANGLE"
	
	if cam_context.rotation_axis_angle[0] != 0 :
		
		rotation = math.degrees(cam_context.rotation_axis_angle[0])
		rot_x = cam_context.rotation_axis_angle[1]
		rot_y = -1 * cam_context.rotation_axis_angle[2]
		rot_z = cam_context.rotation_axis_angle[3]
		pbrtfile.write('Rotate %f %f %f %f\n' % (rotation, rot_x, rot_y, rot_z))

	translate_x = cam_context.location[0]
	translate_y = -1 * cam_context.location[1]
	translate_z = cam_context.location[2]

	pbrtfile.write('Translate %f %f %f\n' % (translate_x, translate_y, translate_z))
	

	pbrtfile.write('Camera ')
	if(camera.type == "PERSP"):
		pbrtfile.write ('\"perspective\" ')

	pbrtfile.write('\"float fov\" [%f]\n\n' % math.degrees(camera.angle / 2.0))

def get_lights():
	
	if renderlayer.use_sky :
		
		world = bpy.data.worlds["World"]
		worldnodes = world.node_tree.nodes
		background_node = worldnodes.get("Background") 
		strength = background_node.inputs[1].default_value 
		begin_attribute()
		indent()
		pbrtfile.write('LightSource \"infinite\" \"string mapname\" \"%s\"\n' % env)
		indent()
		pbrtfile.write('\"color scale\" [%f %f %f]\n' % (strength, strength, strength))
		end_attribute()		
	
	all_lamps = bpy.data.lamps 
	for index in range (len(all_lamps)):

		lamp = all_lamps[index]
		if lamp.type == "AREA":
			
			lamp_color = lamp.color 
		
			if bpy.ops.cycles.use_shading_nodes: 
				em_node = lamp.node_tree.nodes.get("Emission")
				lamp_color = em_node.inputs[0].default_value[0] * em_node.inputs[1].default_value

			
			begin_attribute()
			indent()
			pbrtfile.write('AreaLightSource \"diffuse\" \"rgb L\" [%f %f %f]\n' % (lamp_color, lamp_color, lamp_color))
			indent()
			pbrtfile.write('Shape \"disk\" \"float radius\" [%f]\n' % lamp.size)
			end_attribute()


def make_geometry_folder():
	os.chdir(path_to_dir)
	os.system("mkdir geometry")
	return "%sgeometry" % path_to_dir

def get_materials(mesh):
	print("materials coming soon.")


def get_geometry(): 	
	geometry_dir = make_geometry_folder()
	all_objects = bpy.data.meshes
	print(all_objects)
	
	for index in range (len(all_objects)):

		if use_obj : 
			print("useobj")

		else: 
			newply = "%s/%s.ply" % (geometry_dir, all_objects[index].name)
			bpy.ops.export_mesh.ply(filepath=newply, check_existing=True, axis_forward='Y', axis_up='Z', filter_glob="*.ply", use_mesh_modifiers=True, use_normals=True, use_uv_coords=True, use_colors = True, global_scale=1)
			begin_attribute()
			indent()
			pbrtfile.write('Shape \"plymesh\" \"string filename\" \"geometry/%s.ply\"\n' % all_objects[index].name)
			get_materials(all_objects[index])
			end_attribute()

def get_attributes(): 
	
	pbrtfile.write('WorldBegin\n\n')
	get_lights()
	get_geometry()
	pbrtfile.write('WorldEnd')

def write_scene():
	get_integrator()
	get_sampler()
	get_film()
	get_camera()
	get_attributes()

def run_pbrt():
	os.system("which pbrt")
	os.chdir("%s" % path_to_dir)
	os.system("pwd")
	os.system("pbrt %s" % pbrtfilename)
	os.system("open %s" % userinput)

def main(): 
	
	write_scene()

	

main()
pbrtfile.close()
#run_pbrt()