def codename_to_label(codename):
    rremove = '_project'
    if codename.endswith(rremove):
        codename = codename[:len(codename)-len(rremove)]
    codename = codename\
        .split('.')[1]\
        .replace('_', ' ')\
        .capitalize()
    return codename

