import pandas as pd
import statsmodels.api as sm

import hnelib.pandas


def get_logits(
    df,
    endog,
    exog,
    groupby_cols=[],
    add_constant=True,
):
    if isinstance(exog, str):
        exog = [exog]

    df = df.copy()

    df, original_cols, groupby_cols = hnelib.pandas._get_original_and_groupby_cols(df, groupby_cols)

    df = df[groupby_cols + exog + [endog]]

    result_keys = [c for c in exog]

    if add_constant:
        result_keys = ['const'] + result_keys

    logit_rows = []
    for _, rows in df.groupby(groupby_cols):
        Y = rows[endog]
        X = rows[exog]

        if add_constant:
            X = sm.add_constant(X)

        model_result = sm.Logit(Y, X).fit(disp=False)

        logit_row = hnelib.pandas._get_groupby_info(rows, groupby_cols, original_cols)

        for key in result_keys:
            logit_row[key] = model_result.params[key]
            logit_row[f"{key}-P"] = model_result.pvalues[key]

        logit_rows.append(logit_row)

    return pd.DataFrame(logit_rows)


def get_logit_predictions(
    logit_model,
    df_to_predict,
    add_constant=True,
):
    df_to_predict = df_to_predict.copy()

    model_cols = list(df_to_predict.columns)

    if add_constant:
        df_to_predict = sm.add_constant(df_to_predict)
        model_cols = ['const'] + model_cols

    model = sm.Logit([1 for i in range(len(df_to_predict))], df_to_predict)

    model_params = [logit_model[c] for c in model_cols]

    return list(model.predict(model_params, df_to_predict))
