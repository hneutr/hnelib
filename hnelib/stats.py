from scipy.stats import pearsonr

def correlation(xs, ys):
    pearson, pearson_p = pearsonr(xs, ys)
    return pearson, pearson_p
