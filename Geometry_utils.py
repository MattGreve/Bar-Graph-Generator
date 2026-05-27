"""
Geometry_utils.py
-----------------
Core geometry builders for the modular bar graph tool.
Handles 3D generation, validation, and routes requests via the dispatcher.
"""

import maya.cmds as cmds

# Import material module
try:
    import Material_utils
    import importlib
    importlib.reload(Material_utils)
except ImportError as e:
    cmds.warning(f"Could not import Material_utils. Ensure it is in the same directory: {e}")

# Global debug flag
DEBUG = True

def _print_debug(msg):
    """Internal helper to print debug messages if DEBUG is True."""
    if DEBUG:
        print(f"[DEBUG] {msg}")

# ─────────────────────────────────────────────
#  BUILDER FUNCTIONS
# ─────────────────────────────────────────────

def build_bar(data, context=None):
    """
    Builds a single 3D bar, assigns dynamic color, and routes label creation.
    """
    if context is None:
        context = {}
        
    label = data.get("label", "Unknown")
    value = data.get("value", 0)
    x_pos = data.get("x_pos", 0)
    
    # Input Validation: Catch negative values
    if value < 0:
        cmds.warning(f"Negative value ({value}) detected for '{label}'. Clamping to 0.01.")
        value = 0.01

    v_scale = context.get("value_scale", 0.05)
    b_width = context.get("bar_width", 1.0)
    height = max(value * v_scale, 0.01)
    
    try:
        safe_label = str(label).replace(" ", "_")
        bar = cmds.polyCube(name=f"{safe_label}_bar", w=b_width, h=height, d=b_width)[0]
        cmds.move(x_pos, height * 0.5, 0, bar, absolute=True)
        
        # Route to Material_utils
        rgb = Material_utils.calculate_color(value, context.get("min", 0), context.get("max", 1), context.get("avg", 0.5))
        Material_utils.apply_material(bar, safe_label, rgb)
        
        _print_debug(f"Built bar: {safe_label} at X:{x_pos} with Value:{value}")
        
        # Label creation
        label_data = {"type": "label", "text": label, "x_pos": x_pos}
        lbl_node = create_element(label_data, context)
        
        return [bar, lbl_node] if lbl_node else [bar]
        
    except Exception as e:
        cmds.warning(f"Error building bar '{label}': {e}")
        return []

def build_label(data, context=None):
    """Builds a text curve label for a specific graph element."""
    text = str(data.get("text", "Label"))
    x = data.get("x_pos", 0)
    
    try:
        curves = cmds.textCurves(f=True, t=text)
        grp = cmds.group(curves, name=f"{text}_label_GRP")
        cmds.xform(grp, centerPivots=True)
        
        bb = cmds.exactWorldBoundingBox(grp)
        width = bb[3] - bb[0]
        cmds.move(x - width * 0.5, -0.3, 0, grp, absolute=True)
        cmds.scale(0.15, 0.15, 0.15, grp)
        _print_debug(f"Built label: {text}")
        return grp
    except Exception as e:
        cmds.warning(f"Error building label '{text}': {e}")
        return None

def build_ground(data, context=None):
    """Builds the foundation plane for the graph."""
    if context is None:
        context = {}
        
    total_w = context.get("total_width", 10.0)
    try:
        ground = cmds.polyPlane(name="BarGraph_ground", w=total_w + 2, h=4, sx=1, sy=1)[0]
        cmds.move(total_w * 0.5 - 0.5, 0, 0, ground, absolute=True)
        Material_utils.apply_material(ground, "Ground", (0.1, 0.1, 0.1))
        _print_debug(f"Built ground plane with width {total_w + 2}")
        return ground
    except Exception as e:
        cmds.warning(f"Error building ground: {e}")
        return None

def build_avg_line(data, context=None):
    """Builds a NURBS curve spanning the graph to indicate the dataset average."""
    if context is None:
        context = {}
        
    avg_val = context.get("avg", 0)
    v_scale = context.get("value_scale", 0.05)
    total_w = context.get("total_width", 10.0)
    y_pos = avg_val * v_scale
    
    try:
        crv = cmds.curve(name="Average_Line_CRV", d=1, p=[(-1.0, y_pos, 0.5), (total_w, y_pos, 0.5)])
        cmds.setAttr(f"{crv}Shape.overrideEnabled", 1)
        cmds.setAttr(f"{crv}Shape.overrideColor", 17) # Yellow override
        _print_debug(f"Built average line at Y:{y_pos}")
        return crv
    except Exception as e:
        cmds.warning(f"Error building average line: {e}")
        return None

# ─────────────────────────────────────────────
#  DISPATCHER
# ─────────────────────────────────────────────

BUILDERS = {
    "bar": build_bar,
    "label": build_label,
    "ground": build_ground,
    "avg_line": build_avg_line
}

def create_element(element_data, context=None):
    """Routes an element dictionary to the appropriate builder function."""
    elem_type = element_data.get("type")
    
    if not elem_type:
        cmds.warning("Element data missing 'type' key.")
        return None
        
    builder_func = BUILDERS.get(elem_type)
    
    if not builder_func:
        cmds.warning(f"Unknown element type: '{elem_type}'. Skipping.")
        return None
        
    try:
        return builder_func(element_data, context)
    except Exception as e:
        cmds.warning(f"Critical failure in dispatcher for type '{elem_type}': {e}")
        return None
