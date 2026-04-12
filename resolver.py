def resolve_file(filepath, mode="ours"):
    with open(filepath, "r") as f:
        lines = f.readlines()
    
    out = []
    in_conflict = False
    keep_block = False
    
    for line in lines:
        if line.startswith("<<<<<<< HEAD"):
            in_conflict = True
            keep_block = (mode == "ours")
            continue
        elif line.startswith("======="):
            keep_block = (mode == "theirs")
            continue
        elif line.startswith(">>>>>>>"):
            in_conflict = False
            keep_block = False
            continue
            
        if not in_conflict or keep_block:
            out.append(line)
            
    with open(filepath, "w") as f:
        f.writelines(out)

resolve_file("frontend/scholara_v3.py", "ours")
