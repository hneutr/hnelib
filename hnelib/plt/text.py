def fraction(numerator, denominator, convert_hyphens=True):
    string = r"$\frac{\mathrm{" + numerator + "}}{\mathrm{" + denominator + "}}$"

    string = string.replace(' ', '\ ')

    if convert_hyphens:
        string = string.replace("-", u"\u2010")

    return string
