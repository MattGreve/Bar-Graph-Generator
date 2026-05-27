"""
Material_utils.py
-----------------
Handles all shader generation and color math for the modular bar graph tool.
Calculates dynamic colors based on input stats.
"""

import maya.cmds as cmds
import colorsys

def calculate_color(value, min_val, max_val, avg_val):
    """
    Calculates an RGB color based on where the value sits relative to the average.
    Red (0.0) for minimum, Yellow (0.16) for average, Green (0.33) for maximum.
    """
    try:
        # Clamp value just in case
        value = max(min_val, min(value, max_val))
        
        if value == avg_val:
            hue = 0.16
        elif value > avg_val:
            range_val = max_val - avg_val
            percent = (value - avg_val) / range_val if range_val else 0
            hue = 0.16 + (percent * 0.17) # Map to green
        else:
            range_val = avg_val - min_val
            percent = (value - min_val) / range_val if range_val else 0
            hue = 0.0 + (percent * 0.16)  # Map to red
            
        return colorsys.hsv_to_rgb(hue, 0.8, 0.85)
    except Exception as e:
        cmds.warning(f"Color calculation failed: {e}. Defaulting to gray.")
        return (0.5, 0.5, 0.5)


def apply_material(node, name, rgb_color):
    """Creates and assigns a Lambert material to a node."""
    try:
        shader = cmds.shadingNode("lambert", asShader=True, name=name + "_MAT")
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name + "_SG")
        cmds.connectAttr(shader + ".outColor", sg + ".surfaceShader", force=True)
        cmds.setAttr(shader + ".color", rgb_color[0], rgb_color[1], rgb_color[2], type="double3")
        cmds.sets(node, edit=True, forceElement=sg)
    except Exception as e:
        cmds.warning(f"Failed to apply material to {node}: {e}")
