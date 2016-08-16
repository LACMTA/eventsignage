def getSuffix(n):
    if (4 <= dayint <= 20) or (24 <= dayint <= 30):
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][dayint % 10 - 1]
    return suffix
