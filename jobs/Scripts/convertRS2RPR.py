
'''
Redshift to RadeonProRender Converter

History:
v.1.0 - first version
v.1.1 - IBL issue, Displacement convertopn in rsMatarial
v.1.2 - Link To Reflaction convertion change in rsMaterial
v.1.3 - Area light convertion
v.1.4 - Ambient Occlusion, Fresnel support
v.1.5 - Clean scene from redshift (dialog)
v.1.6 - Redshift Material Blender convertation, updated all material convertation
v.1.7 - Fix bugs, deleting lights with transforms.
v.1.8 - Opacity convertation in Redshift Material, rsColorLayer support.
v.1.9 - Fix area light conversion
v.2.0 - Add bumpBlend support
v.2.1 - Fix bug with channel converting, fix bug with creating extra materials.
v.2.2 - ColorCorrection support. Update physical light & subsurface material conversion.
v.2.3 - rsVolumeScattering conversion
v.2.4 - Added the ability to re-convert scene
v.2.5 - RedshiftArchitectural conversion updates.
v.2.6 - RedshiftIncandescent conversion updates.
v.2.7 - RedshiftMaterial & RedshiftSubSurface conversion updates
v.2.8 - RedshiftIESLight & RedshiftPortalLight conversion
v.2.9 - Fresnel mode & ss units mode conversion updates in RedshiftMaterial 
        Conversion of light units
        Update conversion of color+edge tint mode in RedshiftMaterial, VolumeScattering update
        Update conversion of metalness in RedshiftArchitectural
        Multiscatter layers conversion update in RedshiftMaterial
v.2.10 - Intensity conversion in dome light
        Intensity conversion in Redshift Environment
        Update conversion of fresnel modes in RedshiftMaterial
v.2.11 - Fix displacement conversion in Redshift Material
        Update image unit type conversion in physical light
v.2.12 - Update units type of physical light conversion

'''

import maya.mel as mel
import maya.cmds as cmds
import time
import math


# log functions

def write_converted_property_log(rpr_name, rs_name, rpr_attr, rs_attr):

	try:
		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write("    property " + rs_name + "." + rs_attr + " converted to " + rpr_name + "." + rpr_attr + "   \r\n")
	except Exception:
		print("Error writing logs. Scene is not saved")

def write_own_property_log(text):

	try:
		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write("    " + text + "   \r\n")
	except Exception:
		print("Error writing logs. Scene is not saved")

def start_log(rs, rpr):

	try:
		text  = "Found node: \r\n    name: " + rs + "\r\n"
		text += "type: " + cmds.objectType(rs) + "\r\n"
		text += "Converting to: \r\n    name: " + rpr + "\r\n"
		text += "type: " + cmds.objectType(rpr) + "\r\n"
		text += "Conversion details: \r\n"

		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write(text)
	except Exception:
		print("Error writing logs. Scene is not saved")


def end_log(rs):

	try:
		text  = "Conversion of " + rs + " is finished.\n\n"
		text += "\r\n"

		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write(text)
	except Exception:
		print("Error writing logs. Scene is not saved")

# additional fucntions

def copyProperty(rpr_name, rs_name, rpr_attr, rs_attr):

	# full name of attribute
	rs_field = rs_name + "." + rs_attr
	rpr_field = rpr_name + "." + rpr_attr

	try:
		listConnections = cmds.listConnections(rs_field)
	except Exception:
		print("There is no {} field in this node. Check the field and try again. ".format(rs_field))
		write_own_property_log("There is no {} field in this node. Check the field and try again. ".format(rs_field))
		return

	if listConnections:
		source = cmds.connectionInfo(rs_field, sourceFromDestination=True).split('.')
		source = convertRSMaterial(source[0], source[1])
		try:
			cmds.connectAttr(source, rpr_field, force=True)
			write_converted_property_log(rpr_name, source[0], rpr_attr, source[1])
		except Exception:
			print("Connection {} to {} failed. Check the connectors. ".format(source, rpr_field))
			write_own_property_log("Connection {} to {} failed. Check the connectors. ".format(source, rpr_field))
	else:
		setProperty(rpr_name, rpr_attr, getProperty(rs_name, rs_attr))
		write_converted_property_log(rpr_name, rs_name, rpr_attr, rs_attr)


def setProperty(rpr_name, rpr_attr, value):

	# full name of attribute
	rpr_field = rpr_name + "." + rpr_attr

	if type(value) == tuple:
		try:
			cmds.setAttr(rpr_field, value[0], value[1], value[2])
			write_own_property_log("Set value {} to {}.".format(value, rpr_field))
		except Exception:
			print("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))
			write_own_property_log("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))
	else:
		try:
			cmds.setAttr(rpr_field, value)
			write_own_property_log("Set value {} to {}.".format(value, rpr_field))
		except Exception:
			print("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))
			write_own_property_log("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))


def getProperty(material, attr):

	# full name of attribute
	field = material + "." + attr
	try:
		value = cmds.getAttr(field)
		if type(value) == list:
			value = value[0]
	except Exception as ex:
		print(ex)
		write_own_property_log("There is no {} field in this node. Check the field and try again. ".format(field))
		return

	return value

def mapDoesNotExist(rpr_name, rs_name, rpr_attr, rs_attr):

	# full name of attribute
	rs_field = rs_name + "." + rs_attr
	rpr_field = rpr_name + "." + rpr_attr

	try:
		listConnections = cmds.listConnections(rs_field)
	except Exception as ex:
		print(ex)
		write_own_property_log("There is no {} field in this node. Check the field and try again. ".format(rs_field))
		return

	if listConnections:
		source = cmds.connectionInfo(rs_field, sourceFromDestination=True)
		print("Connection {} to {} isn't available. Map isn't supported in this field.".format(source, rpr_field))
		write_own_property_log("Connection {} to {} isn't available. Map isn't supported for this field.".format(source, rpr_field))
		return 0

	return 1



# dispalcement convertion
def convertDisplacement(rs_sg, rpr_name):

	try:
		displacement = cmds.listConnections(rs_sg, type="RedshiftDisplacement")
		if displacement:
			displacement_file = cmds.listConnections(displacement[0], type="file") 
			if displacement_file:
				setProperty(rpr_name, "displacementEnable", 1)
				cmds.connectAttr(displacement_file[0] + ".outColor", rpr_name + ".displacementMap", f=True)
				copyProperty(rpr_name, displacement[0], "displacementMax", "scale")

				meshs = cmds.listConnections(rs_sg, type="mesh")
				if meshs:
					shapes = cmds.listRelatives(meshes[0], type="mesh")
					if shapes: 
						rsEnableSubdivision = getProperty(shapes[0], "rsEnableSubdivision")
						rsEnableDisplacement = getProperty(shapes[0], "rsEnableDisplacement")
						if rsEnableSubdivision and rsEnableDisplacement: 
							copyProperty(rpr_name, shapes[0], "displacementSubdiv", "rsMaxTessellationSubdivs")
	except Exception as ex:
		print(ex)
		print("Failed to convert displacement for {} material".format(rpr_name))


# re-convert is not fully supported for this node (only scale field)
def convertRedshiftNormalMap(rs, source):

	if cmds.objExists(rs + "_rpr"):
		rpr = rs + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRNormal", asUtility=True)
		cmds.rename(rpr, rs + "_rpr")
		rpr = rs + "_rpr"
		file = cmds.shadingNode("file", asTexture=True, isColorManaged=True)
		texture = cmds.shadingNode("place2dTexture", asUtility=True)

		cmds.connectAttr(texture + ".coverage", file + ".coverage", f=True)
		cmds.connectAttr(texture + ".translateFrame", file + ".translateFrame", f=True)
		cmds.connectAttr(texture + ".rotateFrame", file + ".rotateFrame", f=True)
		cmds.connectAttr(texture + ".mirrorU", file + ".mirrorU", f=True)
		cmds.connectAttr(texture + ".mirrorV", file + ".mirrorV", f=True)
		cmds.connectAttr(texture + ".stagger", file + ".stagger", f=True)
		cmds.connectAttr(texture + ".wrapU", file + ".wrapU", f=True)
		cmds.connectAttr(texture + ".wrapV", file + ".wrapV", f=True)
		cmds.connectAttr(texture + ".repeatUV", file + ".repeatUV", f=True)
		cmds.connectAttr(texture + ".offset", file + ".offset", f=True)
		cmds.connectAttr(texture + ".rotateUV", file + ".rotateUV", f=True)
		cmds.connectAttr(texture + ".noiseUV", file + ".noiseUV", f=True)
		cmds.connectAttr(texture + ".vertexUvOne", file + ".vertexUvOne", f=True)
		cmds.connectAttr(texture + ".vertexUvTwo", file + ".vertexUvTwo", f=True)
		cmds.connectAttr(texture + ".vertexUvThree", file + ".vertexUvThree", f=True)
		cmds.connectAttr(texture + ".vertexCameraOne", file + ".vertexCameraOne", f=True)
		cmds.connectAttr(texture + ".outUV", file + ".uv")
		cmds.connectAttr(texture + ".outUvFilterSize", file + ".uvFilterSize")
		cmds.connectAttr(file + ".outColor", rpr + ".color", f=True)

		try:
			cmds.setAttr(file + ".fileTextureName", getProperty(rs, "tex0"), type="string")
			write_converted_property_log(rpr, rs, "fileTextureName", "tex0")
		except Exception as ex:
			print(ex)
			print("Error convertion file texture map")

	# Logging to file (start)
	start_log(rs, rpr)

	copyProperty(rpr, rs, "strength", "scale")

	# Logging to file (end)
	end_log(rs)

	conversion_map = {
		"outDisplacementVector": "out",
		"outDisplacementVectorR": "outR",
		"outDisplacementVectorG": "outG",
		"outDisplacementVectorB": "outB"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertRedshiftAmbientOcclusion(rs, source):

	if cmds.objExists(rs + "_rpr"):
		rpr = rs + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRAmbientOcclusion", asUtility=True)
		cmds.rename(rpr, rs + "_rpr")
		rpr = rs + "_rpr"

	# Logging to file
	start_log(rs, rpr)

	# Fields conversion
	copyProperty(rpr, rs, "unoccludedColor", "bright")
	copyProperty(rpr, rs, "occludedColor", "dark")
	copyProperty(rpr, rs, "radius", "spread")

	# Logging to file
	end_log(rs)

	conversion_map = {
		"outColor": "output",
		"outColorR": "outputR",
		"outColorG": "outputG",
		"outColorB": "outputB"
	}

	rpr += "." + source
	return rpr


# re-convert for ior in unsupported
def convertRedshiftFresnel(rs, source):

	if cmds.objExists(rs + "_rpr"):
		rpr = rs + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRBlendValue", asUtility=True)
	
		fresnel = cmds.shadingNode("RPRFresnel", asUtility=True)
		cmds.rename(fresnel, rs + "_rpr")
		fresnel = rs + "_rpr"

		cmds.connectAttr(fresnel + ".out", rpr + ".weight", f=True)

		copyProperty(fresnel, rs, "ior", "ior")

	# Logging to file
	start_log(rs, rpr)

	# Fields conversion
	copyProperty(rpr, rs, "inputA", "facing_color")
	copyProperty(rpr, rs, "inputB", "perp_color")

	# Logging to file
	end_log(rs)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outR",
		"outColorG": "outG",
		"outColorB": "outB"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertRedshiftColorCorrection(rs, source):

	if cmds.objExists(rs + "_rpr"):
		rpr = rs + "_rpr"
	else:
		rpr = cmds.shadingNode("colorCorrect", asUtility=True)
		cmds.rename(rpr, rs + "_rpr")
		rpr = rs + "_rpr"

	# Logging to file
	start_log(rs, rpr)

	# Fields conversion
	copyProperty(rpr, rs, "inColor", "input")
	copyProperty(rpr, rs, "hueShift", "hue")
	copyProperty(rpr, rs, "satGain", "saturation")
	copyProperty(rpr, rs, "valGain", "level")

	# gamma conversion. Doesn't support map conversion.
	if mapDoesNotExist(rpr, rs, "gamma", "colGamma"):
		gamma = getProperty(rs, "gamma")
		colGamma = (gamma, gamma, gamma)
		setProperty(rpr, "colGamma", colGamma)

	# Logging to file
	end_log(rs)

	rpr += "." + source
	return rpr


def convertRedshiftBumpMap(rs, source):

	if cmds.objExists(rs + "_rpr"):
		rpr = rs + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRBump", asUtility=True)
		cmds.rename(rpr, rs + "_rpr")
		rpr = rs + "_rpr"

	# Logging to file
	start_log(rs, rpr)

	# Fields conversion
	try:
		source_input = cmds.connectionInfo(rs + ".input", sourceFromDestination=True)
		if source_input:
			cmds.connectAttr(rpr + ".color", source_input, force=True)
			write_converted_property_log(rpr, rs, "color", source_input)
	except Exception as ex:
		print(ex)
		print("Failed to convert bump map.")
	
	copyProperty(rpr, rs, "strength", "scale")

	# Logging to file
	end_log(rs)

	rpr += "." + source
	return rpr


def convertRedshiftColorLayer(rs, source):

	if cmds.objExists(rs + "_rpr"):
		rpr = rs + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRBlendMaterial", asShader=True)
		cmds.rename(rpr, rs + "_rpr")
		rpr = rs + "_rpr"

	# Logging to file
	start_log(rs, rpr)

	# Fields conversion
	copyProperty(rpr, rs, "color0", "base_color")
	copyProperty(rpr, rs, "color1", "layer1_color")
	copyProperty(rpr, rs, "weight", "layer1_mask")

	# Logging to file
	end_log(rs)

	rpr += "." + source
	return rpr


def convertRedshiftBumpBlender(rs, source):

	if cmds.objExists(rs + "_rpr"):
		rpr = rs + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRBump", asUtility=True)
		cmds.rename(rpr, rs + "_rpr")
		rpr = rs + "_rpr"

		rpr_blend = cmds.shadingNode("RPRBlendMaterial", asShader=True)
		cmds.connectAttr(rpr_blend + ".outColor", rpr + ".color", force=True)

	try:
		rsBump0 = cmds.listConnections(rs + ".baseInput", type="RedshiftBumpMap")
		if rsBump0:
			valueInput0 = cmds.listConnections(rsBump0[0] + ".input")
			if valueInput0:
				cmds.connectAttr(valueInput0[0] + ".outColor", rpr_blend + ".color0", force=True)
		rsBump1 = cmds.listConnections(rs + ".bumpInput0", type="RedshiftBumpMap")
		if rsBump1:
			valueInput1 = cmds.listConnections(rsBump1[0] + ".input")
			if valueInput1:
				cmds.connectAttr(valueInput1[0] + ".outColor", rpr_blend + ".color1", force=True)

	except Exception as ex:
		print(ex)
		print("Failed to convert bump blender inputs")
	
	conversion_map = {
		"outColor": "out",
		"outColorR": "outR",
		"outColorG": "outG",
		"outColorB": "outB"
	}

	rpr += "." + conversion_map[source]
	return rpr	


######################## 
## RedshiftArchitectural 
########################

def convertRedshiftArchitectural(rsMaterial, source):

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)
		
	# Enable properties, which are default in RedShift
	defaultEnable(rprMaterial, rsMaterial, "diffuse", "diffuse_weight")
	defaultEnable(rprMaterial, rsMaterial, "reflections", "reflectivity")
	defaultEnable(rprMaterial, rsMaterial, "refraction", "transparency")
	defaultEnable(rprMaterial, rsMaterial, "emissive", "incandescent_scale")
	defaultEnable(rprMaterial, rsMaterial, "clearCoat", "refl_base")

	# Logging to file
	start_log(rsMaterial, rprMaterial)

	# diffuse
	copyProperty(rprMaterial, rsMaterial, "diffuseColor", "diffuse") 
	copyProperty(rprMaterial, rsMaterial, "diffuseWeight", "diffuse_weight")
	copyProperty(rprMaterial, rsMaterial, "diffuseRoughness", "diffuse_roughness")

	# translucency conversion
	translucency_enable = getProperty(rsMaterial, "refr_translucency")
	if translucency_enable:
		setProperty(rprMaterial, "separateBackscatterColor", 1)
		copyProperty(rprMaterial, rsMaterial, "backscatteringColor", "refr_trans_color")
		copyProperty(rprMaterial, rsMaterial, "backscatteringWeight", "refr_trans_weight")
	
	# primary reflection
	copyProperty(rprMaterial, rsMaterial, "reflectColor", "refl_color") 
	copyProperty(rprMaterial, rsMaterial, "reflectWeight", "reflectivity")
	copyProperty(rprMaterial, rsMaterial, "reflectIOR", "brdf_fresnel_ior")

	if mapDoesNotExist(rprMaterial, rsMaterial, "reflectRoughness", "refl_gloss"):  
		gloss = 1 - getProperty(rsMaterial, "refl_gloss")
		setProperty(rprMaterial, "reflectRoughness", gloss)

	copyProperty(rprMaterial, rsMaterial, "reflectAnisotropy", "anisotropy") 
	copyProperty(rprMaterial, rsMaterial, "reflectAnisotropyRotation", "anisotropy_rotation")

	setProperty(rprMaterial, "reflectMetalMaterial", getProperty(rsMaterial, "refl_is_metal"))

	brdf_fresnel_type = getProperty(rsMaterial, "brdf_fresnel_type")
	if brdf_fresnel_type: # conductor
		brdf_extinction_coeff = getProperty(rsMaterial, "brdf_extinction_coeff")
		if brdf_extinction_coeff > 2:
			setProperty(rprMaterial, "reflectMetalMaterial", 1)
			setProperty(rprMaterial, "reflectMetalness", 1)
			copyProperty(rprMaterial, rsMaterial, "reflectColor", "diffuse")
		
	# sec reflection
	copyProperty(rprMaterial, rsMaterial, "coatWeight", "refl_base") 
	copyProperty(rprMaterial, rsMaterial, "coatColor", "refl_base_color")
		
	# refraction
	copyProperty(rprMaterial, rsMaterial, "refractColor", "refr_color")
	copyProperty(rprMaterial, rsMaterial, "refractWeight", "transparency")

	if mapDoesNotExist(rprMaterial, rsMaterial, "refractRoughness", "refr_gloss"):   
		gloss = 1 - getProperty(rsMaterial, "refr_gloss")
		setProperty(rprMaterial, "refractRoughness", gloss)
			
	fog_enable = getProperty(rsMaterial, "refr_falloff_on")
	if fog_enable:
		copyProperty(rprMaterial, rsMaterial, "refractAbsorptionDistance", "refr_falloff_dist")
	
	end_color_enable = getProperty(rsMaterial, "refr_falloff_color_on")
	if end_color_enable:
		copyProperty(rprMaterial, rsMaterial, "refractAbsorbColor", "refr_falloff_color") 
	else: 
		copyProperty(rprMaterial, rsMaterial, "refractAbsorbColor", "refr_color")
	
	setProperty(rprMaterial, "refractAllowCaustics", getProperty(rsMaterial, "do_refractive_caustics"))
		
	# emissive
	copyProperty(rprMaterial, rsMaterial, "emissiveColor", "additional_color")
	copyProperty(rprMaterial, rsMaterial, "emissiveWeight", "incandescent_scale")

	setProperty(rprMaterial, "transparencyEnable", 1)
	if mapDoesNotExist(rprMaterial, rsMaterial, "transparencyLevel", "cutout_opacity"):  
		opacity = 1 - getProperty(rsMaterial,  "cutout_opacity")
		setProperty(rprMaterial, "transparencyLevel", opacity)
			
	# Logging in file
	end_log(rsMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


#######################
## RedshiftCarPaint 
#######################

def convertRedshiftCarPaint(rsMaterial, source):

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Enable properties, which are default in RedShift
	defaultEnable(rprMaterial, rsMaterial, "diffuse", "diffuse_weight")
	defaultEnable(rprMaterial, rsMaterial, "reflections", "spec_weight")
	defaultEnable(rprMaterial, rsMaterial, "clearCoat", "clearcoat_weight")

	# Logging to file
	start_log(rsMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, rsMaterial, "diffuseColor", "base_color")
	copyProperty(rprMaterial, rsMaterial, "diffuseWeight", "diffuse_weight")
	copyProperty(rprMaterial, rsMaterial, "reflectColor", "spec_color")
	copyProperty(rprMaterial, rsMaterial, "reflectWeight", "spec_weight")
	copyProperty(rprMaterial, rsMaterial, "coatColor", "clearcoat_color")
	copyProperty(rprMaterial, rsMaterial, "coatWeight", "clearcoat_weight")

	# Logging in file
	end_log(rsMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


#######################
## RedshiftHair 
####################### 

def convertRedshiftHair(rsMaterial, source):

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Logging to file
	start_log(rsMaterial, rprMaterial)

	# no_rpr_analog for rsHair
	# will be created empty uber material

	# Logging to file
	end_log(rsMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


######################## 
## RedshiftIncandescent 
########################

def convertRedshiftIncandescent(rsMaterial, source):

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Enable properties, which are default in RedShift
	setProperty(rprMaterial, "diffuse", 0)
	setProperty(rprMaterial, "transparencyEnable", 1)
	defaultEnable(rprMaterial, rsMaterial, "emissive", "intensity")

	# Logging to file
	start_log(rsMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, rsMaterial, "emissiveIntensity", "intensity")
	copyProperty(rprMaterial, rsMaterial, "transparencyLevel", "alpha")

	setProperty(rprMaterial, "emissiveDoubleSided", getProperty(rsMaterial, "doublesided"))

	transparencyLevel = 1 - getProperty(rsMaterial, "alpha")
	setProperty(rprMaterial, "transparencyLevel", transparencyLevel)

	# converting temperature to emissive color
	# no_rpr_analog
	color_mode = getProperty(rsMaterial, "colorMode")
	if color_mode:
		temperature = getProperty(rsMaterial, "temperature") / 100

		if temperature <= 66:
			colorR = 255
		else:
			colorR = temperature - 60
			colorR = 329.698727446 * colorR ** -0.1332047592
			if colorR < 0:
				colorR = 0
			if colorR > 255:
				colorR = 255


		if temperature <= 66:
			colorG = temperature
			colorG = 99.4708025861 * math.log(colorG) - 161.1195681661
			if colorG < 0:
				colorG = 0
			if colorG > 255:
				colorG = 255
		else:
			colorG = temperature - 60
			colorG = 288.1221695283 * colorG ** -0.0755148492
			if colorG < 0:
				colorG = 0
			if colorG > 255:
				colorG = 255


		if temperature >= 66:
			colorB = 255
		elif temperature <= 19:
			colorB = 0
		else:
			colorB = temperature - 10
			colorB = 138.5177312231 * math.log(colorB) - 305.0447927307
			if colorB < 0:
				colorB = 0
			if colorB > 255:
				colorB = 255

		colorR = colorR / 255
		colorG = colorG / 255
		colorB = colorB / 255

		setProperty(rprMaterial, "emissiveColor", (colorR, colorG, colorB))

	else:
		copyProperty(rprMaterial, rsMaterial, "emissiveColor", "color")

	# Logging to file
	end_log(rsMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial



###################### 
## RedshiftMaterial 
###################### 

def convertRedshiftMaterial(rsMaterial, source):

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

			convertDisplacement(materialSG, rprMaterial)

	# Enable properties, which are default in RedShift.
	defaultEnable(rprMaterial, rsMaterial, "diffuse", "diffuse_weight")
	defaultEnable(rprMaterial, rsMaterial, "reflections", "refl_weight")
	defaultEnable(rprMaterial, rsMaterial, "refraction", "refr_weight")
	defaultEnable(rprMaterial, rsMaterial, "clearCoat", "coat_weight")
	defaultEnable(rprMaterial, rsMaterial, "emissive", "emission_weight")
	defaultEnable(rprMaterial, rsMaterial, "sssEnable", "ms_amount")

	# Logging to file
	start_log(rsMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, rsMaterial, "diffuseColor", "diffuse_color")
	copyProperty(rprMaterial, rsMaterial, "diffuseWeight", "diffuse_weight")
	copyProperty(rprMaterial, rsMaterial, "diffuseRoughness", "diffuse_roughness")

	copyProperty(rprMaterial, rsMaterial, "reflectWeight", "refl_weight")
	copyProperty(rprMaterial, rsMaterial, "reflectRoughness", "refl_roughness")
	copyProperty(rprMaterial, rsMaterial, "reflectAnisotropy", "refl_aniso")
	copyProperty(rprMaterial, rsMaterial, "reflectAnisotropyRotation", "refl_aniso_rotation")

	# Fresnel type conversion
	refl_reflectivity = getProperty(rsMaterial, "refl_reflectivity")
	refl_fr_mode = getProperty(rsMaterial, "refl_fresnel_mode" )

	if refl_fr_mode == 3:
		copyProperty(rprMaterial, rsMaterial, "reflectIOR", "refl_ior")
		copyProperty(rprMaterial, rsMaterial, "reflectColor", "refl_color")

	elif refl_fr_mode == 2:

		try:
			blend_value = cmds.shadingNode("RPRBlendValue", asUtility=True)
			cmds.connectAttr(blend_value + ".out", rprMaterial + ".reflectColor", f=True)

			# blend color from diffuse and reflectivity to reflect color
			# no_rpr_analog

			copyProperty(blend_value, rsMaterial, "inputA", "refl_reflectivity")
			copyProperty(blend_value, rsMaterial, "inputB", "diffuse_color")
			copyProperty(blend_value, rsMaterial, "weight", "refl_metalness")

			metalness = getProperty(rsMaterial, "refl_metalness")
			if metalness > 0:
				setProperty(rprMaterial, "reflectMetalMaterial", 1)
				copyProperty(rprMaterial, rsMaterial, "reflectMetalness", "refl_metalness")
		except Exception as ex:
			print(ex)
			print("Error while metall fresnel mode conversion")

	# no_rpr_analog
	elif refl_fr_mode == 1:

		edge_tint = getProperty(rsMaterial, "refl_edge_tint")

		arithmetic = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.connectAttr(arithmetic + ".out", rprMaterial + ".reflectColor", f=True)

		blend_value = cmds.shadingNode("RPRBlendValue", asUtility=True)
		cmds.connectAttr(blend_value + ".out", arithmetic + ".inputB", f=True)

		fresnel = cmds.shadingNode("RPRFresnel", asUtility=True)
		cmds.connectAttr(fresnel + ".out", blend_value + ".weight", f=True)

		copyProperty(arithmetic, rsMaterial, "inputA", "refl_color")
		setProperty(arithmetic, "operation", 2)

		setProperty(fresnel, "ior", 1.5)

		if edge_tint[0] or edge_tint[1] or edge_tint[2]:

			copyProperty(blend_value, rsMaterial, "inputA", "refl_reflectivity")
			copyProperty(blend_value, rsMaterial, "inputB", "refl_edge_tint")

			setProperty(rprMaterial, "reflectMetalMaterial", 1)
			copyProperty(rprMaterial, rsMaterial, "reflectMetalness", "refl_metalness")
			if getProperty(rprMaterial, "reflectMetalness") != 1:
				setProperty(rprMaterial, "reflectMetalness", 1)

		else:

			copyProperty(blend_value, rsMaterial, "inputA", "refl_reflectivity")
			copyProperty(blend_value, rsMaterial, "inputB", "refl_color")

			max_refl = max(refl_reflectivity)
			if max_refl == 1:
				max_refl = 0.9999
			elif max_refl == 0:
				max_refl = 0.0001

			ior = -1 * (max_refl + 1 + 2 * math.sqrt(max_refl) / (max_refl - 1))
			if ior > 10:
				ior = 10

			setProperty(rprMaterial, "reflectIOR", ior)
			

	else:
		# advanced ior
		# no_rpr_analog
		# take one channel from advanced ior ti rpr ior
		copyProperty(rprMaterial, rsMaterial, "reflectIOR", "refl_ior30")
		copyProperty(rprMaterial, rsMaterial, "reflectColor", "refl_color")

	copyProperty(rprMaterial, rsMaterial, "refractColor", "refr_color")
	copyProperty(rprMaterial, rsMaterial, "refractWeight", "refr_weight")
	copyProperty(rprMaterial, rsMaterial, "refractRoughness", "refr_roughness")
	copyProperty(rprMaterial, rsMaterial, "refractIor", "refr_ior")
	copyProperty(rprMaterial, rsMaterial, "refractLinkToReflect", "refr_use_base_IOR")
	copyProperty(rprMaterial, rsMaterial, "refractThinSurface", "refr_thin_walled")

	# maps doesn't support ( will work incorrectly )
	ss_unitsMode = getProperty(rsMaterial, "ss_unitsMode")
	if ss_unitsMode:
		if mapDoesNotExist(rprMaterial, rsMaterial, "refractAbsorbColor", "ss_extinction_coeff"):
			ss_ext_coeff = getProperty(rsMaterial, "ss_extinction_coeff")
			absorb_color = (1 - ss_ext_coeff[0], 1 - ss_ext_coeff[1], 1 - ss_ext_coeff[2])
			setProperty(rprMaterial, "refractAbsorbColor", absorb_color)

		if mapDoesNotExist(rprMaterial, rsMaterial, "refractAbsorptionDistance", "ss_extinction_scale"):
			absorption = 1 / getProperty(rsMaterial,  "ss_extinction_scale")
			setProperty(rprMaterial, "refractAbsorptionDistance", absorption)

	else:
		copyProperty(rprMaterial, rsMaterial, "refractAbsorbColor", "refr_transmittance")
		if mapDoesNotExist(rprMaterial, rsMaterial, "refractAbsorptionDistance", "refr_absorption_scale"):
			absorption = 1 / getProperty(rsMaterial, "refr_absorption_scale")
			setProperty(rprMaterial, "refractAbsorptionDistance", absorption)

	copyProperty(rprMaterial, rsMaterial, "coatColor", "coat_color")
	copyProperty(rprMaterial, rsMaterial, "coatWeight", "coat_weight")
	copyProperty(rprMaterial, rsMaterial, "coatRoughness", "coat_roughness")
	copyProperty(rprMaterial, rsMaterial, "coatTransmissionColor", "coat_transmittance")

	coat_fr_mode = getProperty(rsMaterial, "coat_fresnel_mode")
	if coat_fr_mode == 3:
		copyProperty(rprMaterial, rsMaterial, "coatIor", "coat_ior")

	copyProperty(rprMaterial, rsMaterial, "emissiveColor", "emission_color")
	copyProperty(rprMaterial, rsMaterial, "emissiveWeight", "emission_weight")
	copyProperty(rprMaterial, rsMaterial, "emissiveIntensity", "emission_weight")

	copyProperty(rprMaterial, rsMaterial, "backscatteringWeight", "ms_amount")
	copyProperty(rprMaterial, rsMaterial, "sssWeight", "ms_amount")

	ms_amount = getProperty(rsMaterial, "ms_amount")
	if ms_amount:
		scatter_color = []
		ms_weight0 = getProperty(rsMaterial, "ms_weight0")
		ms_weight1 = getProperty(rsMaterial, "ms_weight1")
		ms_weight2 = getProperty(rsMaterial, "ms_weight2")
		count = 3
		if not ms_weight0:
			count -= 1
		if not ms_weight1:
			count -= 1
		if not ms_weight2:
			count -= 1

		color0 = getProperty(rsMaterial, "ms_color0")
		color1 = getProperty(rsMaterial, "ms_color1")
		color2 = getProperty(rsMaterial, "ms_color2")
		scatter_color.append((color0[0] * ms_weight0 + color1[0] * ms_weight1 + color2[0] * ms_weight2) / count)
		scatter_color.append((color0[1] * ms_weight0 + color1[1] * ms_weight1 + color2[1] * ms_weight2) / count)
		scatter_color.append((color0[2] * ms_weight0 + color1[2] * ms_weight1 + color2[2] * ms_weight2) / count)
		setProperty(rprMaterial, "volumeScatter", tuple(scatter_color))

		radius = []
		ms_radius0 = getProperty(rsMaterial, "ms_radius0")
		ms_radius1 = getProperty(rsMaterial, "ms_radius1")
		ms_radius2 = getProperty(rsMaterial, "ms_radius2")
		ms_radius_scale = getProperty(rsMaterial, "ms_radius_scale")
		avg_radius = (ms_radius0 * ms_weight0 + ms_radius1 * ms_weight1 + ms_radius2 * ms_weight2) / count
		radius.append((avg_radius + scatter_color[0]) * ms_radius_scale * ms_amount)
		radius.append((avg_radius + scatter_color[1]) * ms_radius_scale * ms_amount)
		radius.append((avg_radius + scatter_color[2]) * ms_radius_scale * ms_amount)
		setProperty(rprMaterial, "subsurfaceRadius", tuple(radius))

	backscatteringWeight = getProperty(rsMaterial, "transl_weight")
	if backscatteringWeight:
		setProperty(rprMaterial, "separateBackscatterColor", 1)
		copyProperty(rprMaterial, rsMaterial, "backscatteringColor", "transl_color")
		copyProperty(rprMaterial, rsMaterial, "backscatteringWeight", "transl_weight")

	# Opacity convert. Material conversion doesn't support, because all rsMaterial have outColor, but we need outAlpha.
	if mapDoesNotExist(rprMaterial, rsMaterial, "transparencyLevel", "opacity_color"):
		rs_opacity = getProperty(rsMaterial, "opacity_color")
		max_value = 1 - max(rs_opacity)
		setProperty(rprMaterial, "transparencyLevel", max_value)

	try:
		bumpConnections = cmds.listConnections(rsMaterial + ".bump_input")
		if bumpConnections:
			setProperty(rprMaterial, "normalMapEnable", 1)
			copyProperty(rprMaterial, rsMaterial, "normalMap", "bump_input")
	except Exception as ex:
		write_own_property_log("Failed to convert bump.")

	# Logging to file
	end_log(rsMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial



##########################
## RedshiftMaterialBlender 
##########################

def convertRedshiftMaterialBlender(rsMaterial, source): 

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRBlendMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Logging to file
	start_log(rsMaterial, rprMaterial)  

	# Fields conversion
	copyProperty(rprMaterial, rsMaterial, "color0", "baseColor")
	copyProperty(rprMaterial, rsMaterial, "color1", "layerColor1")

	# weight conversion
	try:
		listConnections = cmds.listConnections(rsMaterial + ".blendColor1")
		if listConnections:
			cmds.connectAttr(listConnections[0] + ".outAlpha", rprMaterial + ".weight", force=True)
			write_own_property_log("Created connection from {} to {}. ".format(listConnections[0] + ".outAlpha", rprMaterial + ".weight"))
	except Exception as ex:
		print(ex)
		print("Failed to convert weight map.")
		write_own_property_log("Failed to convert weight map.")

	# Logging to file
	end_log(rsMaterial) 

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


#############################
## RedshiftMatteShadowCatcher 
#############################

def convertRedshiftMatteShadowCatcher(rsMaterial, source):  

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRShadowCatcherMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Logging to file
	start_log(rsMaterial, rprMaterial)  

	# Fields conversion
	copyProperty(rprMaterial, rsMaterial, "bgIsEnv", "backgroundIsEnv")
	copyProperty(rprMaterial, rsMaterial, "shadowTransp", "transparency")
	copyProperty(rprMaterial, rsMaterial, "bgColor", "background")
	copyProperty(rprMaterial, rsMaterial, "shadowColor", "shadows")
		
	# Logging to file
	end_log(rsMaterial) 

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


######################## 
## RedshiftShaderSwitch 
######################## 

def convertRedshiftShaderSwitch(rsMaterial, source): 

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Logging to file
	start_log(rsMaterial, rprMaterial)  

	# no_rpr_analog
	# empty uber will be created

	# Logging to file
	end_log(rsMaterial) 

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


######################
## RedshiftSkin 
##################### 

def convertRedshiftSkin(rsMaterial, source): 

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Logging to file
	start_log(rsMaterial, rprMaterial)  

	# no_rpr_analog
	# empty uber will be created

	# Logging to file
	end_log(rsMaterial) 

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial



####################### 
## RedshiftSprite 
####################### 

def convertRedshiftSprite(rsMaterial, source): 

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Logging to file
	start_log(rsMaterial, rprMaterial)  

	# no_rpr_analog
	# empty uber will be created

	# Logging to file
	end_log(rsMaterial) 

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial



############################
## RedshiftSubSurfaceScatter 
############################ 

def convertRedshiftSubSurfaceScatter(rsMaterial, source):  

	materialSG = cmds.listConnections(rsMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(rsMaterial + "_rpr"):
		rprMaterial = rsMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsMaterial + "_rpr"))
		rprMaterial = rsMaterial + "_rpr"

		# Check shading engine in rsMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)
		 
	
	# Enable properties, which are default in RedShift
	setProperty(rprMaterial, "sssEnable", 1)
	setProperty(rprMaterial, "separateBackscatterColor", 1)
	setProperty(rprMaterial, "reflections", 1)
		
	# Logging to file
	start_log(rsMaterial, rprMaterial)   

	# Fields conversion
	setProperty(rprMaterial, "diffuseWeight", 0.2)
	setProperty(rprMaterial, "backscatteringWeight", 0.8)
	copyProperty(rprMaterial, rsMaterial, "reflectIOR", "ior")
	copyProperty(rprMaterial, rsMaterial, "diffuseColor", "sub_surface_color")
	copyProperty(rprMaterial, rsMaterial, "volumeScatter", "sub_surface_color")
	copyProperty(rprMaterial, rsMaterial, "backscatteringColor", "scatter_color")

	if mapDoesNotExist(rprMaterial, rsMaterial, "subsurfaceRadius", "scatter_color"):   
		radius = getProperty(rsMaterial, "scatter_radius")
		scatterColor= getProperty(rsMaterial, "scatter_color")
		sssRadius = [radius + scatterColor[0] * 1.5, radius + scatterColor[1], radius + scatterColor[2]]
		setProperty(rprMaterial, "subsurfaceRadius", tuple(sssRadius))
		
	if mapDoesNotExist(rprMaterial, rsMaterial, "reflectRoughness", "refl_gloss"):  
		gloss = 1 - getProperty(rsMaterial, "refl_gloss")
		setProperty(rprMaterial, "reflectRoughness", gloss)
	   
	# Logging to file
	end_log(rsMaterial) 

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


def convertRedshiftPhysicalSky(sky):
	
	if cmds.objExists("RPRSky"):
		skyNode = "RPRSkyShape"
	else:
		# create RPRSky node
		skyNode = cmds.createNode("RPRSky", n="RPRSkyShape")
  
	# Logging to file
	start_log(sky, skyNode)

	# Copy properties from rsPhysicalSky
	setProperty(skyNode, "turbidity", getProperty(sky, "haze"))
	setProperty(skyNode, "intensity", getProperty(sky, "multiplier"))
	setProperty(skyNode, "groundColor", getProperty(sky, "ground_color"))
	setProperty(skyNode, "filterColor", getProperty(sky, "night_color"))
	setProperty(skyNode, "sunDiskSize", getProperty(sky, "sun_disk_scale"))
	setProperty(skyNode, "sunGlow", getProperty(sky, "sun_glow_intensity"))

	# Logging to file
	end_log(sky)  


def convertRedshiftEnvironment(env):

	if cmds.objExists("RPRIBL"):
		iblShape = "RPRIBLShape"
		iblTransform = "RPRIBL"
	else:
		# create IBL node
		iblShape = cmds.createNode("RPRIBL", n="RPRIBLShape")
		iblTransform = cmds.listRelatives(iblShape, p=True)[0]
		setProperty(iblTransform, "scaleX", 1001.25663706144)
		setProperty(iblTransform, "scaleY", 1001.25663706144)
		setProperty(iblTransform, "scaleZ", 1001.25663706144)

	# Logging to file 
	start_log(env, iblShape)
  
	# display IBL option
	exposure = getProperty(env, "exposure0")
	setProperty(iblShape, "intensity", 1 * 2 ** exposure)

	copyProperty(iblShape, env, "display", "backPlateEnabled")

	# Copy properties from rsEnvironment
	try:
		envTransform = cmds.listConnections("rsEnvironment1", type="place3dTexture")[0]
		setProperty(iblTransform, "rotateX", getProperty(envTransform, "rotateX"))
		setProperty(iblTransform, "rotateY", getProperty(envTransform, "rotateY"))
		setProperty(iblTransform, "rotateZ", getProperty(envTransform, "rotateZ"))
	except Exception as ex:
		print(ex)
		print("Failed to convert rotate properties from Redshift Environment")
	
	try:
		texMode = getProperty(env, "texMode")
		if not texMode:
			ibl_map = getProperty(env, "tex0")
			cmds.setAttr(iblTransform + ".filePath", ibl_map, type="string")
	except Exception as ex:
		print(ex)
		print("Failed to convert map from Redshift Environment")
		   
	# Logging to file
	end_log(env)  


def convertRedshiftDomeLight(dome_light):

	if cmds.objExists("RPRIBL"):
		iblShape = "RPRIBLShape"
		iblTransform = "RPRIBL"
	else:
		# create IBL node
		iblShape = cmds.createNode("RPRIBL", n="RPRIBLShape")
		iblTransform = cmds.listRelatives(iblShape, p=True)[0]
		setProperty(iblTransform, "scaleX", 1001.25663706144)
		setProperty(iblTransform, "scaleY", 1001.25663706144)
		setProperty(iblTransform, "scaleZ", 1001.25663706144)

	# Logging to file 
	start_log(dome_light, iblShape)

	# display IBL option
	exposure = getProperty(dome_light, "exposure0")
	setProperty(iblShape, "intensity", 1 * 2 ** exposure)

	copyProperty(iblShape, dome_light, "display", "background_enable")

	try:
		ibl_map = getProperty(dome_light, "tex0")
		cmds.setAttr(iblTransform + ".filePath", ibl_map, type="string")
	except Exception as ex:
		print(ex)
		print("Failed to convert map from Redshift Environment")
	
	domeTransform = cmds.listRelatives(dome_light, p=True)[0]
	rotateY = getProperty(domeTransform, "rotateY") - 90
	setProperty(domeTransform, "rotateY", rotateY)

	# Logging to file
	end_log(dome_light)  


def convertRedshiftPhysicalLight(rs_light):

	# Redshift light transform
	rsTransform = cmds.listRelatives(rs_light, p=True)[0]
	rsLightShape = rs_light.split("|")[-1]

	if cmds.objExists(rsLightShape + "_rpr"):
		rprLightShape = rsLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
	else: 
		rprLightShape = cmds.createNode("RPRPhysicalLight", n="RPRPhysicalLightShape")
		cmds.rename(rprLightShape, rsLightShape + "_rpr")
		rprLightShape = rsLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		cmds.rename(rprTransform, rsTransform + "_rpr")
		rprTransform = rsTransform + "_rpr"

	# Logging to file 
	start_log(rsLightShape, rprLightShape)

	# Copy properties from rsLight
	copyProperty(rprTransform, rsTransform, "translateX", "translateX")
	copyProperty(rprTransform, rsTransform, "translateY", "translateY")
	copyProperty(rprTransform, rsTransform, "translateZ", "translateZ")
	copyProperty(rprTransform, rsTransform, "rotateX", "rotateX")
	copyProperty(rprTransform, rsTransform, "rotateY", "rotateY")
	copyProperty(rprTransform, rsTransform, "rotateZ", "rotateZ")
	copyProperty(rprTransform, rsTransform, "scaleX", "scaleX")
	copyProperty(rprTransform, rsTransform, "scaleY", "scaleY")
	copyProperty(rprTransform, rsTransform, "scaleZ", "scaleZ")

	lightType = getProperty(rs_light, "lightType")
	light_type_map = {
		0:0, # area
		1:2, # point
		2:1, # spot
		3:3  # directional
	}
	setProperty(rprLightShape, "lightType", light_type_map[lightType])
	
	color_mode_map = {
		0:0, # color
		1:1, # temperature
		2:1  # temperature and color #no_rpr_analog
	}
	setProperty(rprLightShape, "colorMode", color_mode_map[getProperty(rs_light, "colorMode")])

	areaShape = getProperty(rs_light, "areaShape")
	if lightType == 0: #area
		area_shape_map = {
			0:3,   # rectangle
			1:0,   # disc
			2:2,   # sphere
			3:1,   # cylinder
			4:4    # mesh 
		}
		setProperty(rprLightShape, "areaLightShape", area_shape_map[areaShape])

	intensity = getProperty(rs_light, "intensity")
	exposure = getProperty(rs_light, "exposure")
	unitsType = getProperty(rs_light, "unitsType")
	if unitsType == 0: #image 
		scale_multiplier = getProperty(rsTransform, "scaleX") * getProperty(rsTransform, "scaleY")
		if lightType == 0: #area #image -> lumen
			if areaShape in (0, 1): # rectangle or disk
				setProperty(rprLightShape, "intensityUnits", 0)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 2500 * scale_multiplier)
			elif areaShape == 2: # sphere
				setProperty(rprLightShape, "intensityUnits", 0)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 1000 * scale_multiplier)
			elif areaShape == 3: # cylinder
				copyProperty(rprTransform, rsTransform, "scaleX", "scaleZ")
				copyProperty(rprTransform, rsTransform, "scaleZ", "scaleX")
				setProperty(rprTransform, "rotateY", getProperty(rsTransform, "rotateY") + 90)
				setProperty(rprTransform, "rotateX", 0)
				scale_multiplier = getProperty(rsTransform, "scaleX") * getProperty(rsTransform, "scaleY")
				setProperty(rprLightShape, "intensityUnits", 0)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 335 * scale_multiplier)
			elif areaShape == 4: # mesh
				setProperty(rprLightShape, "intensityUnits", 0)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 1000 * scale_multiplier)
		elif lightType == 1: #point #image -> lumen
			setProperty(rprLightShape, "intensityUnits", 0)
			setProperty(rprLightShape, "lightIntensity", (intensity *  2 ** exposure) / (2500 * (1 + intensity *  2 ** exposure / 10000)))
		elif lightType == 2: #spot #image -> lumen
			setProperty(rprLightShape, "intensityUnits", 0)
			setProperty(rprLightShape, "lightIntensity", (intensity *  2 ** exposure) / (3000 * (1 + intensity *  2 ** exposure / 10000)))
		elif lightType == 3: # directional #image -> luminance
			setProperty(rprLightShape, "intensityUnits", 1)
			setProperty(rprLightShape, "lightIntensity", intensity * 3.3333)
	elif unitsType == 1: #luminous 
		if lightType == 0: #area 
			if areaShape in (0, 1, 2): # rectangle  disk sphere
				setProperty(rprLightShape, "intensityUnits", 0)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 30000)
			elif areaShape == 3: # cylinder
				copyProperty(rprTransform, rsTransform, "scaleX", "scaleZ")
				copyProperty(rprTransform, rsTransform, "scaleZ", "scaleX")
				setProperty(rprTransform, "rotateY", getProperty(rsTransform, "rotateY") + 90)
				setProperty(rprTransform, "rotateX", 0)
				setProperty(rprLightShape, "intensityUnits", 0)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 15000)
			elif areaShape == 4: # mesh
				setProperty(rprLightShape, "intensityUnits", 0)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 15000)
		elif lightType in (1, 2): #point and spot #luminous -> lumen
			setProperty(rprLightShape, "intensityUnits", 0)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 10000)
		elif lightType == 3: #directional  #luminous -> luminance
			setProperty(rprLightShape, "intensityUnits", 1)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure)
	elif unitsType == 2: #luminance -> luminance
		if lightType == 0: #area 
			if areaShape in (0, 1, 2): # rectangle  disk sphere
				setProperty(rprLightShape, "intensityUnits", 1)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 10000)
			elif areaShape == 3: # cylinder
				copyProperty(rprTransform, rsTransform, "scaleX", "scaleZ")
				copyProperty(rprTransform, rsTransform, "scaleZ", "scaleX")
				setProperty(rprTransform, "rotateY", getProperty(rsTransform, "rotateY") + 90)
				setProperty(rprTransform, "rotateX", 0)
				setProperty(rprLightShape, "intensityUnits", 1)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 5000)
			elif areaShape == 4: # mesh
				setProperty(rprLightShape, "intensityUnits", 1)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 5000)
		elif lightType == 1: #point #luminous -> lumen
			setProperty(rprLightShape, "intensityUnits", 0)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 30000000)
		elif lightType == 2: #spot #luminous -> lumen
			setProperty(rprLightShape, "intensityUnits", 0)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 10000)
		elif lightType == 3: #directional
			setProperty(rprLightShape, "intensityUnits", 1)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 3000)
	elif unitsType == 3: #radiant power -> watts
		if lightType == 0: #area 
			if areaShape in (0, 1, 2): # rectangle  disk sphere
				setProperty(rprLightShape, "intensityUnits", 2)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 45)
				copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
			elif areaShape == 3: # cylinder
				copyProperty(rprTransform, rsTransform, "scaleX", "scaleZ")
				copyProperty(rprTransform, rsTransform, "scaleZ", "scaleX")
				setProperty(rprTransform, "rotateY", getProperty(rsTransform, "rotateY") + 90)
				setProperty(rprTransform, "rotateX", 0)
				setProperty(rprLightShape, "intensityUnits", 2)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 20)
				copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
			elif areaShape == 4: # mesh
				setProperty(rprLightShape, "intensityUnits", 2)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 20)
				copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
		elif lightType in (1, 2): # point and spot #radiant power -> watts
			setProperty(rprLightShape, "intensityUnits", 2)
			setProperty(rprLightShape, "lightIntensity", (intensity *  2 ** exposure) / (15 * (0.92 + intensity *  2 ** exposure / 10000)))
			copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
		elif lightType == 3: #directional #radiant power -> luminance
			setProperty(rprLightShape, "intensityUnits", 1)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure * 20)
			copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
	elif unitsType == 4: #radiance - > radiance
		if lightType == 0: #area 
			if areaShape in (0, 1, 2): # rectangle  disk sphere
				setProperty(rprLightShape, "intensityUnits", 3)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 15)
				copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
			elif areaShape == 3: # cylinder
				copyProperty(rprTransform, rsTransform, "scaleX", "scaleZ")
				copyProperty(rprTransform, rsTransform, "scaleZ", "scaleX")
				setProperty(rprTransform, "rotateY", getProperty(rsTransform, "rotateY") + 90)
				setProperty(rprTransform, "rotateX", 0)
				setProperty(rprLightShape, "intensityUnits", 3)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 9)
				copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
			elif areaShape == 4: # mesh
				setProperty(rprLightShape, "intensityUnits", 3)
				setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 9)
				copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")
		elif lightType in (1, 2): #point and spot #radiance - > watts
			setProperty(rprLightShape, "intensityUnits", 2)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 44444.44444)
			copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")	
		elif lightType == 3: #directional #radiance - > radiance
			setProperty(rprLightShape, "intensityUnits", 3)
			setProperty(rprLightShape, "lightIntensity", intensity *  2 ** exposure / 5)
			copyProperty(rprLightShape, rs_light, "luminousEfficacy", "lumensperwatt")	

	if lightType == 0:
		copyProperty(rprLightShape, rs_light, "areaLightVisible", "areaVisibleInRender")
	elif lightType == 2:
		angle = getProperty(rs_light, "spotConeAngle")
		falloffAngle = getProperty(rs_light, "spotConeFalloffAngle")
		falloffCurve = getProperty(rs_light, "spotConeFalloffCurve")

		if falloffAngle*falloffCurve < falloffAngle*math.cos(falloffAngle):
			setProperty(rprLightShape, "spotLightOuterConeFalloff", angle + falloffAngle*falloffCurve)
			setProperty(rprLightShape, "spotLightInnerConeAngle", angle - falloffAngle*falloffCurve)
		elif falloffAngle*falloffCurve < 2*angle:
			outerConeFalloff = angle + falloffAngle*math.cos(falloffAngle)
			setProperty(rprLightShape, "spotLightOuterConeFalloff", outerConeFalloff)
			innerConeAngle = angle - falloffAngle*falloffCurve
			if innerConeAngle < 0:
				innerConeAngle = 0
			elif innerConeAngle > outerConeFalloff:
				innerConeAngle = outerConeFalloff
			setProperty(rprLightShape, "spotLightInnerConeAngle", innerConeAngle)
		else:
			outerConeFalloff = angle + falloffAngle*math.cos(falloffAngle)
			setProperty(rprLightShape, "spotLightOuterConeFalloff", outerConeFalloff)
			setProperty(rprLightShape, "spotLightInnerConeAngle", outerConeFalloff / 2)

	copyProperty(rprLightShape, rs_light, "colorPicker", "color")
	copyProperty(rprLightShape, rs_light, "temperature", "temperature")


	# Logging to file
	end_log(rsLightShape)  


def convertRedshiftPortalLight(rs_light):

	# Redshift light transform
	rsTransform = cmds.listRelatives(rs_light, p=True)[0]
	rsLightShape = rs_light.split("|")[-1]

	if cmds.objExists(rsLightShape + "_rpr"):
		rprLightShape = rsLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
	else: 
		rprLightShape = cmds.createNode("RPRPhysicalLight", n="RPRPhysicalLightShape")
		cmds.rename(rprLightShape, rsLightShape + "_rpr")
		rprLightShape = rsLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		cmds.rename(rprTransform, rsTransform + "_rpr")
		rprTransform = rsTransform + "_rpr"

	# Logging to file 
	start_log(rsLightShape, rprLightShape)

	# Copy properties from rsLight

	setProperty(rprLightShape, "lightType", 0)

	intensity = getProperty(rs_light, "multiplier")
	exposure = getProperty(rs_light, "exposure")
	setProperty(rprLightShape, "lightIntensity", intensity * 2 ** exposure)
	setProperty(rprLightShape, "intensityUnits", 1)
	
	copyProperty(rprLightShape, rs_light, "colorPicker", "tint_color")

	visible = getProperty(rs_light, "transparency")
	if (visible[0] or visible[1] or visible[2]): 
		setProperty(rprLightShape, "areaLightVisible", 1)
	else:
		setProperty(rprLightShape, "areaLightVisible", 0)
	
	copyProperty(rprTransform, rsTransform, "translateX", "translateX")
	copyProperty(rprTransform, rsTransform, "translateY", "translateY")
	copyProperty(rprTransform, rsTransform, "translateZ", "translateZ")
	copyProperty(rprTransform, rsTransform, "rotateX", "rotateX")
	copyProperty(rprTransform, rsTransform, "rotateY", "rotateY")
	copyProperty(rprTransform, rsTransform, "rotateZ", "rotateZ")
	copyProperty(rprTransform, rsTransform, "scaleX", "scaleX")
	copyProperty(rprTransform, rsTransform, "scaleY", "scaleY")
	copyProperty(rprTransform, rsTransform, "scaleZ", "scaleZ")

	# Logging to file
	end_log(rsLightShape)  


def convertRedshiftIESLight(rs_light): 

	# Redshift light transform
	rsTransform = cmds.listRelatives(rs_light, p=True)[0]
	rsLightShape = rs_light.split("|")[-1]

	if cmds.objExists(rsLightShape + "_rpr"):
		rprLightShape = rsLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
	else: 
		rprLightShape = cmds.createNode("RPRIES", n="RPRIESLight")
		cmds.rename(rprLightShape, rsLightShape + "_rpr")
		rprLightShape = rsLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		cmds.rename(rprTransform, rsTransform + "_rpr")
		rprTransform = rsTransform + "_rpr"

	# Logging to file 
	start_log(rsLightShape, rprLightShape)

	# Copy properties from rsLight
	intensity = getProperty(rs_light, "multiplier")
	exposure = getProperty(rs_light, "exposure")
	setProperty(rprLightShape, "intensity", intensity * 2 ** exposure)
	
	copyProperty(rprLightShape, rs_light, "color", "color")

	try:
		ies = getProperty(rs_light, "profile")
		cmds.setAttr(rprLightShape + ".iesFile", ies, type="string")
	except Exception as ex:
		print(ex)
		print("Failed to convert map from Redshift IES light")
	
	
	copyProperty(rprTransform, rsTransform, "translateX", "translateX")
	copyProperty(rprTransform, rsTransform, "translateY", "translateY")
	copyProperty(rprTransform, rsTransform, "translateZ", "translateZ")
	setProperty(rprTransform, "rotateX", getProperty(rsTransform, "rotateX") + 180)
	copyProperty(rprTransform, rsTransform, "rotateY", "rotateY")
	copyProperty(rprTransform, rsTransform, "rotateZ", "rotateZ")
	copyProperty(rprTransform, rsTransform, "scaleX", "scaleX")
	copyProperty(rprTransform, rsTransform, "scaleY", "scaleY")
	copyProperty(rprTransform, rsTransform, "scaleZ", "scaleZ")

	# Logging to file
	end_log(rsLightShape)  


def convertRedshiftVolumeScattering(rsVolumeScattering):

	# Check material exist
	if cmds.objExists(rsVolumeScattering + "_rpr"):
		rprMaterial = rsVolumeScattering + "_rpr"
	else:
		# Creating new Volume material
		rprMaterial = cmds.shadingNode("RPRVolumeMaterial", asShader=True)
		cmds.rename(rprMaterial, (rsVolumeScattering + "_rpr"))
		rprMaterial = rsVolumeScattering + "_rpr"
		
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		cmds.connectAttr(rprMaterial + ".outColor", sg + ".volumeShader", f=True)

		# create sphere
		cmds.polySphere(n="Volume")
		setProperty("Volume", "scaleX", 999)
		setProperty("Volume", "scaleY", 999)
		setProperty("Volume", "scaleZ", 999)

		# assign material
		cmds.select("Volume")
		cmds.sets(sg, forceElement=True, empty=True)

	# Logging to file 
	start_log(rsVolumeScattering, rprMaterial) 

	# Fields conversion
	copyProperty(rprMaterial, rsVolumeScattering, "scatterColor", "tint")
	copyProperty(rprMaterial, rsVolumeScattering, "scatteringDirection", "phase")
	copyProperty(rprMaterial, rsVolumeScattering, "emissionColor", "fogAmbient")

	density = getProperty(rsVolumeScattering, "scatteringAmount") * 8
	setProperty(rprMaterial, "density", density)
	
	# Logging to file
	end_log(rsVolumeScattering)  


# Convert material. Returns new material name.
def convertRSMaterial(rsMaterial, source):

	rs_type = cmds.objectType(rsMaterial)

	conversion_func = {
		"RedshiftArchitectural": convertRedshiftArchitectural,
		"RedshiftCarPaint": convertRedshiftCarPaint,
		"RedshiftHair": convertRedshiftHair,
		"RedshiftIncandescent": convertRedshiftIncandescent,
		"RedshiftMaterial": convertRedshiftMaterial,
		"RedshiftMaterialBlender": convertRedshiftMaterialBlender,
		"RedshiftMatteShadowCatcher": convertRedshiftMatteShadowCatcher,
		"RedshiftShaderSwitch": convertRedshiftShaderSwitch,
		"RedshiftSkin": convertRedshiftSkin,
		"RedshiftSprite": convertRedshiftSprite,
		"RedshiftSubSurfaceScatter": convertRedshiftSubSurfaceScatter,
		##utilities
		"RedshiftBumpMap": convertRedshiftBumpMap,
		"RedshiftNormalMap": convertRedshiftNormalMap,
		"RedshiftAmbientOcclusion": convertRedshiftAmbientOcclusion,
		"RedshiftFresnel": convertRedshiftFresnel,
		"RedshiftColorLayer": convertRedshiftColorLayer,
		"RedshiftBumpBlender": convertRedshiftBumpBlender,
		"RedshiftColorCorrection": convertRedshiftColorCorrection
	}

	if rs_type in conversion_func:
		rpr = conversion_func[rs_type](rsMaterial, source)
	else:
		if source:
			rpr = rsMaterial + "." + source
		else:
			rpr = ""

	return rpr


# Convert light. Returns new light name.
def convertLight(light):

	rs_type = cmds.objectType(light)

	conversion_func = {
		"RedshiftPhysicalLight": convertRedshiftPhysicalLight,
		"RedshiftDomeLight": convertRedshiftDomeLight,
		"RedshiftPortalLight": convertRedshiftPortalLight,
		#"RedshiftPhysicalSun": convertRedshiftPhysicalSun,
		"RedshiftIESLight": convertRedshiftIESLight,
	}

	conversion_func[rs_type](light)


def searchRedshiftType(obj):

	if cmds.objExists(obj):
		objType = cmds.objectType(obj)
		if "Redshift" in objType:
			return 1
	return 0


def cleanScene():

	listMaterials= cmds.ls(materials=True)
	for material in listMaterials:
		if searchRedshiftType(material):
			shEng = cmds.listConnections(material, type="shadingEngine")
			try:
				cmds.delete(shEng[0])
				cmds.delete(material)
			except Exception as ex:
				print(ex)

	listLights = cmds.ls(l=True, type=["RedshiftDomeLight", "RedshiftIESLight", "RedshiftPhysicalLight", "RedshiftPhysicalSun", "RedshiftPortalLight"])
	for light in listLights:
		transform = cmds.listRelatives(light, p=True)
		try:
			cmds.delete(light)
			cmds.delete(transform[0])
		except Exception as ex:
			print(ex)

	listObjects = cmds.ls(l=True)
	for obj in listObjects:
		if searchRedshiftType(object):
			try:
				cmds.delete(obj)
			except Exception as ex:
				print(ex)


def checkSG(material):

	if searchRedshiftType(material):
		SGs = cmds.listConnections(material, type="shadingEngine")
		if SGs:
			return 1
	return 0


def defaultEnable(RPRmaterial, rsMaterial, enable, value):

	weight = cmds.getAttr(rsMaterial + "." + value)
	if weight > 0:
		cmds.setAttr(RPRmaterial + "." + enable, 1)
	else:
		cmds.setAttr(RPRmaterial + "." + enable, 0)


def convertScene():

	# Check plugins
	if not cmds.pluginInfo("redshift4maya", q=True, loaded=True):
		cmds.loadPlugin("redshift4maya")

	if not cmds.pluginInfo("RadeonProRender", q=True, loaded=True):
		cmds.loadPlugin("RadeonProRender")

	# Convert RedshiftEnvironment
	env = cmds.ls(type="RedshiftEnvironment")
	if env:
		try:
			convertRedshiftEnvironment(env[0])
		except Exception as ex:
			print(ex)
			print("Error while converting environment. ")

	# Convert RedshiftPhysicalSky
	sky = cmds.ls(type="RedshiftPhysicalSky")
	if sky:
		try:
			convertRedshiftPhysicalSky(sky[0])
		except Exception as ex:
			print(ex)
			print("Error while converting physical sky. \n")

	# Convert RedshiftAtmosphere
	atmosphere = cmds.ls(type="RedshiftVolumeScattering")
	if atmosphere:
		try:
			convertRedshiftVolumeScattering(atmosphere[0])
		except Exception as ex:
			print(ex)
			print("Error while converting volume scattering environment.")

	# Get all lights from scene
	listLights = cmds.ls(l=True, type=["RedshiftDomeLight", "RedshiftIESLight", "RedshiftPhysicalLight", "RedshiftPhysicalSun", "RedshiftPortalLight"])

	# Convert lights
	for light in listLights:
		try:
			convertLight(light)
		except Exception as ex:
			print(ex)
			print("Error while converting {} light. \n".format(light))
		

	# Get all materials from scene
	listMaterials = cmds.ls(materials=True)
	materialsDict = {}
	for each in listMaterials:
		if checkSG(each):
			materialsDict[each] = convertRSMaterial(each, "")

	for rs, rpr in materialsDict.items():
		try:
			rs_sg = cmds.listConnections(rs, type="shadingEngine")
			rpr_sg = cmds.listConnections(rpr, type="shadingEngine")
			meshs = cmds.sets(rs_sg, q=True)
			cmds.sets(meshs, e=True, forceElement=rpr_sg[0])
		except Exception as ex:
			print(ex)
			print("Error while converting {} material. \n".format(rs))
	
	cmds.setAttr("defaultRenderGlobals.currentRenderer", "FireRender", type="string")
	setProperty("defaultRenderGlobals", "imageFormat", 8)
	setProperty("RadeonProRenderGlobals", "completionCriteriaIterations", getProperty("redshiftOptions", "progressiveRenderingNumPasses"))


def auto_launch():
	convertScene()
	cleanScene()

def manual_launch():
	print("Convertion start!")
	startTime = 0
	testTime = 0
	startTime = time.time()
	convertScene()
	testTime = time.time() - startTime
	print("Convertion finished! Time: " + str(testTime))

	response = cmds.confirmDialog(title="Convertation finished",
							  message=("Total time: " + str(testTime) + "\nDelete all redshift instances?"),
							  button=["Yes", "No"],
							  defaultButton="Yes",
							  cancelButton="No",
							  dismissString="No")

	if response == "Yes":
		cleanScene()


def onMayaDroppedPythonFile(empty):
	manual_launch()

if __name__ == "__main__":
	manual_launch()



