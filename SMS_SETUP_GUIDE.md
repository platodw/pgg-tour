# 📱 SMS Setup Guide for PGG Tour

## Overview
Your PGG Tour website now sends SMS notifications instead of emails when events are scheduled.

## Step 1: Create Twilio Account

1. Go to: https://www.twilio.com/try-twilio
2. Sign up for a free account
3. Verify your phone number
4. Complete the setup wizard

## Step 2: Get Your Credentials

After signing up, you'll need these 3 pieces of information from your Twilio Console:

1. **Account SID** - Starts with "AC" followed by 32 characters
2. **Auth Token** - Your secret authentication token  
3. **Phone Number** - Your Twilio phone number (starts with +1)

## Step 3: Configure Heroku Environment Variables

1. Go to your Heroku app dashboard
2. Click "Settings" tab
3. Click "Reveal Config Vars"
4. Add these 3 variables with your actual Twilio values:

```
Variable Name: TWILIO_ACCOUNT_SID
Value: [Your Account SID from Twilio Console]

Variable Name: TWILIO_AUTH_TOKEN  
Value: [Your Auth Token from Twilio Console]

Variable Name: TWILIO_PHONE_NUMBER
Value: [Your Twilio phone number with +1]
```

## Step 4: Test SMS Functionality

1. Deploy the updated code to Heroku (should auto-deploy from GitHub)
2. Go to Schedule page on pggtour.com
3. Create a test event with admin password: pgg2024
4. Select players with phone numbers in their roster profiles
5. Submit the event
6. Players should receive SMS notifications!

## Step 5: Phone Number Requirements

Make sure players have phone numbers in their roster profiles in these formats:
- (555) 123-4567
- 555-123-4567  
- 5551234567
- +15551234567

The system automatically formats them for SMS delivery.

## Trial Account Limitations

**Free Trial Includes:**
- $15 in SMS credits (about 2000 messages)
- Can only send to verified phone numbers during trial
- Messages include "Sent from your Twilio trial account"

**To Remove Limitations:**
- Add a credit card to upgrade your account
- Costs about $1-2/month for typical PGG Tour usage

## Cost Estimate

**Typical Usage:**
- 20 players × 2 events/month = 40 SMS messages
- Cost: 40 × $0.0075 = $0.30/month
- Plus Twilio base fee: ~$1/month  
- Total: About $1.30/month

## Troubleshooting

**SMS Not Sending?**
1. Check Heroku app logs for error messages
2. Verify all 3 Twilio config vars are set correctly
3. Ensure players have valid phone numbers in roster
4. During trial, verify recipient numbers in Twilio console

**Need Help?**
- Twilio documentation: https://www.twilio.com/docs/sms
- Make sure all 3 Heroku config variables are set
- Test with your own verified phone number first
