!pip install alpha-vantage
!pip install python-dotenv
from alpha_vantage.timeseries import TimeSeries
# Import API key
from dotenv import load_dotenv
import os
#adds variable from environments
load_dotenv()

def Predict_Stock_Prices():
  # Get stock ticker input from user
  ticker = input('Type the Stock Ticker Label You Would Like To View: ')
  api_key =  os.environ.get("api_key")
  # Pull and update fields from Alpha Vantage
  try:
    ts = TimeSeries(key=api_key, output_format='pandas', indexing_type='integer')
    data, meta_data = ts.get_daily_adjusted(symbol=ticker, outputsize='full')
    data = data.drop(columns=['7. dividend amount','8. split coefficient'])
    df = data.rename(columns={'index':'date','1. open':'open', '2. high':'high', '3. low':'low',
    '4. close':'close','5. adjusted close':'adj close','6. volume':'volume'})
    # Arrange dataframe in sequential index/date order
    df = df[::-1]
    df.reset_index(drop=True, inplace=True)
    df.head()
    df.insert(0,"index", df.index)
    data_set = df
    data_set.head()
    from sklearn.preprocessing import MinMaxScaler
    # Pull close data from dataframe and reshape
    close_data_set = data_set["close"].values.reshape(-1,1)
    dataLength = len(close_data_set)
    # Scale to normalize dataset
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data_set = scaler.fit_transform(close_data_set)
    import math as m
    # split into train and test sets sequentially for LSTM model
    trainSize = m.ceil(int(dataLength * 0.8))
    testSize = int(dataLength) - trainSize
    train_data, test_data = scaled_data_set[0:trainSize,:], scaled_data_set[trainSize:dataLength,:]
    import numpy as np
    xTrain = []
    yTrain = []
    # Amount of prior days to take into account for each day's prediction
    lookbackWindow = 365
    # Loop through data and assign lookback data to "prediction" actual value
    for i in range(lookbackWindow, trainSize):
        xTrain.append(train_data[i-lookbackWindow:i, 0])
        yTrain.append(train_data[i, 0])
    # Reshape lists into arrays for input into LSTM model 
    xTrain, yTrain = np.array(xTrain), np.array(yTrain)
    xTrain = np.reshape(xTrain, (xTrain.shape[0], xTrain.shape[1], 1))
    from keras.models import Sequential
    from keras.layers import LSTM, Dense, Dropout

    # Model starts as sequential and is assigned LSTM, Dropout, and Dense layers (See readme for parameter details)
    model = Sequential()
    model.add(LSTM(50, return_sequences = True, input_shape = (xTrain.shape[1], 1)))
    model.add(LSTM(50))
    model.add(Dense(1))
    # Compile and fit model with train data to be used for predictions
    model.compile(optimizer = 'adam', loss = 'mean_squared_error')
    model.fit(xTrain, yTrain, epochs = 5, batch_size = 32, verbose = 1, validation_split=0.2)

    import numpy as np

    xTest = []
    # Loop through data and assign lookback data to "prediction" true value
    for i in range(lookbackWindow, testSize):
        xTest.append(test_data[i-lookbackWindow:i, 0])
    # Reshape lists into arrays for input into LSTM model     
    xTest = np.array(xTest) 
    xTest = np.reshape(xTest, (xTest.shape[0], xTest.shape[1], 1))
    # Run model to predict stock close price and scale to actual dollar values
    test_data_predictions = model.predict(xTest)
    final_test_predictions = scaler.inverse_transform(test_data_predictions)
  except:
    print(f"Error trying to import {ticker}")

Predict_Stock_Prices()