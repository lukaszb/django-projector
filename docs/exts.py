
def setup(app):
    app.add_crossref_type(
        directivename = "error",
        rolename      = "error",
        indextemplate = "pair: %s; error",
    )
    app.add_crossref_type(
        directivename = "form",
        rolename      = "form",
        indextemplate = "pair: %s; form",
    )
    app.add_crossref_type(
        directivename = "manager",
        rolename      = "manager",
        indextemplate = "pair: %s; manager",
    )
    app.add_crossref_type(
        directivename = "model",
        rolename      = "model",
        indextemplate = "pair: %s; model",
    )
    app.add_crossref_type(
        directivename = "setting",
        rolename      = "setting",
        indextemplate = "pair: %s; setting",
    )
    app.add_crossref_type(
        directivename = "signal",
        rolename      = "signal",
        indextemplate = "pair: %s; signal",
    )
    app.add_crossref_type(
        directivename = "view",
        rolename      = "view",
        indextemplate = "pair: %s; view",
    )

