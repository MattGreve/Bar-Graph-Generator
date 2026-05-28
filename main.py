"""
main.py
-------
Driver script and UI for the bar graph tool.
Collects user input, calculates context bounds, and executes the build loop.
"""

import sys
import os
import maya.cmds as cmds

# Ensure Maya can find our custom modules
current_dir = os.path.dirname(__file__) if "__file__" in locals() else cmds.internalVar(userScriptDir=True)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import Geometry_utils
    import importlib
    importlib.reload(Geometry_utils)
except ImportError as e:
    cmds.warning(f"Could not import Geometry_utils: {e}")

# ─────────────────────────────────────────────
#  DEFAULT DATA
# ─────────────────────────────────────────────
DEFAULT_ROWS = [
    ("Ohtani", "1.066"),
    ("Judge", "1.019"),
    ("Betts", ".987"),
    ("Freeman", ".864"),
    ("League Avg", ".725"),
    ("Replacement", ".600"),
]

# ─────────────────────────────────────────────
#  UI VARIABLES
# ─────────────────────────────────────────────
WIN_ID = "modularBarGraphWin"
MAX_ROWS = 12
_row_fields = []

# ─────────────────────────────────────────────
#  EXECUTION LOGIC
# ─────────────────────────────────────────────

def _collect_data():
    """Reads UI rows and returns a list of dictionaries for the builder."""
    data = []
    for lf, vf in _row_fields:
        if not cmds.textField(lf, exists=True):
            continue
            
        label = cmds.textField(lf, q=True, text=True).strip()
        val_s = cmds.textField(vf, q=True, text=True).strip()
        
        if not label or not val_s:
            continue
            
        try:
            data.append({"type": "bar", "label": label, "value": float(val_s)})
        except ValueError:
            cmds.warning(f"[Bar Graph] '{val_s}' is not a number — row '{label}' skipped.")
    return data

def _on_build(*_):
    """The main driver loop. Compiles config and dispatches to Geometry_utils."""
    config = _collect_data()
    
    if not config:
        cmds.confirmDialog(title="No data", message="Please add at least one valid row.", button=["OK"])
        return

    # Read Settings
    bar_w = cmds.floatSliderGrp("bgBarWidth", q=True, value=True)
    bar_sp = cmds.floatSliderGrp("bgBarSpacing", q=True, value=True)
    v_scale = cmds.floatSliderGrp("bgValueScale", q=True, value=True)
    add_ground = cmds.checkBox("bgAddGround", q=True, value=True)
    
    # Read the custom average target
    add_avg_line = cmds.checkBox("bgAddAvg", q=True, value=True)
    target_avg = cmds.floatField("bgAvgValue", q=True, value=True)
    
    grp_nm = cmds.textField("bgGroupName", q=True, text=True).strip() or "Graph_GRP"

    # Pre-Process: Find bounds for the dynamic color map
    bar_values = [item["value"] for item in config if item.get("value", 0) >= 0]
    
    if not bar_values:
        cmds.warning("No valid positive bar data to build.")
        return
        
    raw_min = min(bar_values)
    raw_max = max(bar_values)
    
    # Anchor the min and max to the target average so the shader math never break if the entire dataset happens to be above or below the target.
    safe_min = min(raw_min, target_avg)
    safe_max = max(raw_max, target_avg)
    
    step = bar_w + bar_sp
    total_width = len(config) * step

    # Setup the context dictionary with the explicit target average
    context = {
        "min": safe_min,
        "max": safe_max,
        "avg": target_avg,
        "value_scale": v_scale,
        "bar_width": bar_w,
        "total_width": total_width - bar_sp
    }

    Geometry_utils._print_debug(f"Context calculated: Min={safe_min}, Max={safe_max}, Target Avg={target_avg}")

    # Inject static elements into the configuration list
    if add_ground:
        config.insert(0, {"type": "ground"})
    if add_avg_line:
        config.append({"type": "avg_line"})

  
    # Main Dispatch Loop
    all_nodes = []
    current_x = 0.0
    
    for entry in config:
        # Placement of bars
        if entry.get("type") == "bar":
            entry["x_pos"] = current_x
            current_x += step
            
        result = Geometry_utils.create_element(entry, context)
        
        if result:
            if isinstance(result, list):
                all_nodes.extend(result)
            else:
                all_nodes.append(result)
                
    # Group everything
    if all_nodes:
        valid_nodes = [node for node in all_nodes if cmds.objExists(node)]
        if valid_nodes:
            cmds.group(valid_nodes, name=grp_nm)
            cmds.select(clear=True)
            print(f"[Bar Graph] Successfully generated: {grp_nm}")

def _add_row(label="", value="", row_layout=None):

     if len(_row_fields) >= MAX_ROWS:
        cmds.warning(f"Maximum {MAX_ROWS} rows reached.")
        return

     if row_layout is None:
        row_layout = "bgRowsLayout"

    cmds.setParent(row_layout)

        row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(220, 120, 30), adjustableColumn=1)

        If = cmds.textField(text=label, placeholderText="Label", width=210)

        vf = cmds.textField(text=value, placeholderText="Value", width=110)

def _remove(*_):
       
       _row_fields[:] = [
            (l, v)
            for l, v in _row_fields
            if l != lf
        ]

         if cmds.rowLayout(row, exists=True):

cmds.deleteUI(row)

    cmds.button(
        label="✕",
        width=24,
        command=_remove,
        annotation="Remove row")

    cmds.setParent("..")

    _row_fields.append((lf, vf))

def _add_calculated_average(*_):
   
    """Calculates the average of all valid entered values
    and adds it as a new graph row."""

    values = []

    # Collect valid numeric values
    for lf, vf in _row_fields:

        if not cmds.textField(vf, exists=True):
            continue

        val_s = cmds.textField(vf, q=True, text=True).strip()

        try:
            values.append(float(val_s))

        except ValueError:
            continue

    # Prevent divide-by-zero
    if not values:
        cmds.warning("[Bar Graph] No valid numeric values found.")
        return

    avg = sum(values) / len(values)

    # Add a new row
    _add_row(
        label="Calculated Avg",
        value=f"{avg:.3f}"
    )

    print(f"[Bar Graph] Added calculated average row: {avg:.3f}")


def _on_clear_all(*_):

    for lf, vf in list(_row_fields):

        parent = cmds.textField(
            lf,
            q=True,
            parent=True
        )

        if cmds.rowLayout(parent, exists=True):
            cmds.deleteUI(parent)

    _row_fields.clear()



# ─────────────────────────────────────────────
#  UI LAYOUT
# ─────────────────────────────────────────────

def _add_row(label="", value="", row_layout=None):
    if len(_row_fields) >= MAX_ROWS:
        cmds.warning(f"Maximum {MAX_ROWS} rows reached.")
        return

    if row_layout is None:
        row_layout = "bgRowsLayout"

    cmds.setParent(row_layout)
    row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(220, 120, 30), adjustableColumn=1)
    
    lf = cmds.textField(text=label, placeholderText="Label", width=210)
    vf = cmds.textField(text=value, placeholderText="Value", width=110)

    def _remove(*_):
        _row_fields[:] = [(l, v) for l, v in _row_fields if l != lf]
        if cmds.rowLayout(row, exists=True):
            cmds.deleteUI(row)

    cmds.button(label="✕", width=24, command=_remove, annotation="Remove row")
    cmds.setParent("..")

    _row_fields.append((lf, vf))


def _on_clear_all(*_):
    for lf, vf in list(_row_fields):
        parent = cmds.textField(lf, q=True, parent=True)
        if cmds.rowLayout(parent, exists=True):
            cmds.deleteUI(parent)
    _row_fields.clear()


def open_ui():
    global _row_fields
    _row_fields = []

    if cmds.window(WIN_ID, exists=True):
        cmds.deleteUI(WIN_ID)

    win = cmds.window(WIN_ID, title="Graph Generator", widthHeight=(440, 580), sizeable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnOffset=("both", 10))

    cmds.separator(height=8, style="none")
    cmds.text(label="Graph Builder", font="boldLabelFont", align="left")
    cmds.text(label="Enter stats. Colors map automatically to your target average.", font="smallPlainLabelFont", align="left")
    cmds.separator(height=10, style="in")

    # Data Rows
    cmds.text(label="Data rows", font="boldLabelFont", align="left")
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(220, 120), adjustableColumn=1, columnAlign2=("left","left"))
    cmds.text(label="  Player / Stat", font="smallBoldLabelFont", width=220)
    cmds.text(label="  Value", font="smallBoldLabelFont", width=120)
    cmds.setParent("..")

    scroll = cmds.scrollLayout("bgScrollArea", height=200, childResizable=True)
    rows_col = cmds.columnLayout("bgRowsLayout", adjustableColumn=True, rowSpacing=3, parent=scroll)

    for lbl, val in DEFAULT_ROWS:
        _add_row(lbl, val, rows_col)

    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200), adjustableColumn=1)
    cmds.button(label="+ Add Row", command=lambda *_: _add_row(row_layout=rows_col))
    cmds.button(label="Clear All", command=_on_clear_all)
    cmds.setParent("..")

    cmds.separator(height=10, style="in")

    # Settings
    cmds.text(label="Settings", font="boldLabelFont", align="left")
    
    # Target Average UI Block
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(180, 80, 60))
    cmds.checkBox("bgAddAvg", label="Draw Target Line", value=True)
    cmds.text(label="Target Stat:")
    cmds.floatField("bgAvgValue", value=0.725, precision=3) # Defaulting to OPS standard
    cmds.setParent("..")
    
    cmds.separator(height=4, style="none")

    cmds.floatSliderGrp("bgBarWidth", label="Bar width", field=True, minValue=0.1, maxValue=5.0, value=1.0, columnWidth3=(120, 60, 180))
    cmds.floatSliderGrp("bgBarSpacing", label="Bar spacing", field=True, minValue=0.0, maxValue=5.0, value=0.4, columnWidth3=(120, 60, 180))
    cmds.floatSliderGrp("bgValueScale", label="Value scale", field=True, minValue=1.0, maxValue=20.0, value=10.0, columnWidth3=(120, 60, 180))

    cmds.separator(height=6, style="none")
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(210, 210))
    cmds.checkBox("bgAddGround", label="Add Ground Plane", value=True)
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(120, 280), adjustableColumn=2, columnAlign2=("left","left"))
    cmds.text(label="Group name", width=120)
    cmds.textField("bgGroupName", text="Graph_GRP", width=270)
    cmds.setParent("..")

    cmds.separator(height=10, style="in")

    # Build
    cmds.button(label="Build Graph", height=36, command=_on_build, backgroundColor=(0.2, 0.6, 0.35))
    cmds.separator(height=8, style="none")

    cmds.showWindow(win)

# ─────────────────────────────────────────────
#  SELF-TEST GUARD
# ─────────────────────────────────────────────
if __name__ == "__main__":
    open_ui()
