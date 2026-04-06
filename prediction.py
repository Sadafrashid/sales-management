import pandas as pd
from sklearn.linear_model import LinearRegression

def predict_sales(sales_data):
    if len(sales_data) < 5:
        return "Need more data"

    df = pd.DataFrame(sales_data, columns=["id","product_id","quantity","total","date"])
    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values("date")
    df["day"] = (df["date"] - df["date"].min()).dt.days

    X = df[["day"]]
    y = df["total"]

    model = LinearRegression()
    model.fit(X, y)

   
    next_day_val = df["day"].max() + 1
    X_new = pd.DataFrame([[next_day_val]], columns=["day"]) 
    
    prediction = model.predict(X_new)
    return round(prediction[0], 2)