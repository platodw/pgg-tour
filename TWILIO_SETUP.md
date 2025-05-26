# 📱 Twilio SMS Setup for PGG Tour

## Step 1: Create Twilio Account

1. **Go to**: https://www.twilio.com/try-twilio
2. **Sign up** for a free account
3. **Verify your phone number**
4. **Complete the setup wizard**

## Step 2: Get Your Credentials

After signing up, you'll need these 3 pieces of information:

1. **Account SID** - Found on your Twilio Console dashboard
2. **Auth Token** - Found on your Twilio Console dashboard
3. **Phone Number** - You'll get a free trial phone number

## Step 3: Configure Heroku Environment Variables

1. **Go to your Heroku app dashboard**
2. **Settings tab** → "Config Vars"
3. **Add these variables**:

```
TWILIO_ACCOUNT_SID = your_account_sid_here
TWILIO_AUTH_TOKEN = your_auth_token_here
TWILIO_PHONE_NUMBER = +1234567890
```

**Example:**
```
TWILIO_ACCOUNT_SID = ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN = your_auth_token_from_twilio_console
TWILIO_PHONE_NUMBER = +15551234567
```

## Step 4: Test SMS Functionality

1. **Deploy the updated code** to Heroku
2. **Go to Schedule page** on pggtour.com
3. **Create a test event** with admin password `pgg2024`
4. **Select players** with phone numbers
5. **Submit** - Players should receive SMS notifications!

## Step 5: Twilio Trial Limitations

**Free Trial Account:**
- ✅ **$15 credit** included
- ✅ **~2000 SMS messages** (at $0.0075 each)
- ⚠️ **Can only text verified numbers** during trial
- ⚠️ **Messages include "Sent from your Twilio trial account"**

**To Remove Limitations:**
- **Upgrade account** (add credit card)
- **$1-2/month** for typical PGG Tour usage
- **No trial restrictions**

## Step 6: Phone Number Format

Players' phone numbers should be in these formats:
- ✅ `(555) 123-4567`
- ✅ `555-123-4567`
- ✅ `5551234567`
- ✅ `+15551234567`

The system automatically formats them for SMS.

## Troubleshooting

### SMS Not Sending?
1. **Check Heroku logs** for error messages
2. **Verify Twilio credentials** in Config Vars
3. **Check phone number format** in roster
4. **Ensure players have phone numbers** entered

### Trial Account Issues?
1. **Verify recipient phone numbers** in Twilio console
2. **Check trial credit balance**
3. **Consider upgrading** to remove restrictions

## Cost Estimate

**Typical PGG Tour Usage:**
- **20 players** × **2 events/month** = 40 SMS/month
- **Cost**: 40 × $0.0075 = $0.30/month
- **Plus Twilio base**: ~$1/month
- **Total**: ~$1.30/month

Very affordable for professional golf group communication!

## Support

If you need help:
1. **Check Twilio documentation**: https://www.twilio.com/docs/sms
2. **Heroku Config Vars**: Make sure all 3 variables are set
3. **Test with your own phone** first during trial
