
def merge_tree_deltas(tree: dict, patch: dict | list) -> dict:
    
    if isinstance(patch, list):
        for single_patch in patch:
            merge_tree_deltas(tree, single_patch)
        return tree
    
    for key, patch_value in patch.items():
        if key in tree:
            tree_value = tree[key]

            if isinstance(tree_value, dict) and isinstance(patch_value, dict):
                merge_tree_deltas(tree_value, patch_value)
            else:
                tree[key] = patch_value
        else:
            tree[key] = patch_value

    return tree