from dash import html

def render_tree(tree):
    
    if isinstance(tree, dict):
        return html.Ul([
            html.Li([
                html.Strong(str(key)),
                render_tree(value)
            ]) for key, value in tree.items()
        ])
    elif isinstance(tree, list):
        return html.Ul([render_tree(item) for item in tree])
    else:
        return html.Pre(str(tree))
    
def render_tree_keys(tree):
    
    if isinstance(tree, dict):
        return html.Ul([
            html.Li([
                html.Strong(str(key)),
                render_tree_keys(value)
            ]) for key, value in tree.items()
        ])
