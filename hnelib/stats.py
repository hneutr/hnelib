from scipy.stats import pearsonr, ks_2samp


def correlation(xs, ys):
    pearson, pearson_p = pearsonr(xs, ys)
    return pearson, pearson_p


def ks_test(dist_1, dist_2, alpha=.05, d_threshold=1.628):
    ks, p = ks_2samp(dist_1, dist_2)

    n = len(dist_1) + len(dist_2)

    ks_threshold = d_threshold * (((2 * n) / (n ** 2)) **.5)

    significant = ks_threshold < abs(ks) and p < alpha

    return p, significant
