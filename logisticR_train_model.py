import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
import joblib

# Load augmented dataset
df = pd.read_csv('Feeding_Dashboard_data_augmented.csv')

# Define features and target
features = ['bmi', 'feed_vol', 'oxygen_flow_rate', 'resp_rate']
target = 'referral'

# Drop missing values
df = df[features + [target]].dropna()

# Separate features and labels
X = df[features]
y = df[target]

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train and test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Train Logistic Regression model
model = LogisticRegression(class_weight='balanced')
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save model and scaler
joblib.dump(model, 'referral_model.pkl')
joblib.dump(scaler, 'referral_scaler.pkl')
print("Model and scaler saved.")
