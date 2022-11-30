import pandas as pd
import statsmodels.api as sm

import hnelib.pd.util
import hnelib.util


CONST_COL = 'const'


def get_logits(
    df,
    endog,
    exog,
    add_constant=True,
    groupby_cols=None,
):
    exog = hnelib.util.as_list(exog)

    df, groupby_cols = hnelib.pd.get_groupby_cols(df, groupby_cols)

    df = df[groupby_cols + exog + [endog]]

    result_keys = [c for c in exog]

    if add_constant:
        result_keys = [CONST_COL] + result_keys

    results = []
    for _, rows in df.groupby(groupby_cols):
        Y = rows[endog]
        X = rows[exog]

        if add_constant:
            X = sm.add_constant(X)

        model = sm.Logit(Y, X).fit(disp=False)

        result = hnelib.pd.util.get_groupby_dict(rows, groupby_cols)

        for key in result_keys:
            result[key] = model.params[key]
            result[f"{key}-P"] = model.pvalues[key]

        results.append(result)

    return pd.DataFrame(results)


def get_logit_predictions(
    model,
    exog,
):
    exog = exog.copy()

    if CONST_COL in model:
        exog = sm.add_constant(exog)

    m = sm.Logit(list(range(len(exog))), exog)

    coefs = [model[c] for c in exog.columns]

    return list(m.predict(coefs, exog))
