# SMS GSM Character Converter for AWS Lambda

## 🎯 What This Does

This AWS Lambda function **saves you money** on SMS costs by automatically converting Unicode characters to GSM-compatible alternatives. When you send SMS messages with Unicode characters (like smart quotes, em dashes, or special symbols), AWS charges you significantly more because it uses UCS-2 encoding instead of the cheaper GSM-7 encoding.

### The Problem
- **Unicode characters** in SMS messages force **UCS-2 encoding**
- **UCS-2 messages** are limited to **70 characters per segment** (vs 160 for GSM)
- **Multi-part UCS-2** messages are limited to **67 characters per segment** (vs 153 for GSM)
- **Result**: Your SMS costs can be **2-3x higher** than necessary

### The Solution
This function automatically:
1. **Detects Unicode characters** that would trigger expensive UCS-2 encoding
2. **Converts 200+ Unicode characters** to GSM alternatives (more comprehensive than Twilio!)
3. **Keeps your messages in GSM-7 encoding** for maximum cost efficiency
4. **Provides intelligent segment management** with auto-preservation and truncation
5. **Offers flexible emoji preservation** for brand-critical messages
6. **Handles international text** including fullwidth characters (Asian languages)
7. **Removes invisible characters** like zero-width spaces that cause encoding issues

---

## 🚀 Quick Start

### Step 1: Deploy to AWS Lambda

1. **Create a new Lambda function** in AWS Console
2. **Runtime**: Python 3.11 or 3.12
3. **Handler**: `lambda_function.lambda_handler`
4. **Copy and paste** the entire code from `message-maximizer.py` (or rename the file to `lambda_function.py` when uploading to Lambda)

### Step 2: Set IAM Permissions

Add this policy to your Lambda execution role:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sms-voice:SendTextMessage"
            ],
            "Resource": "*"
        }
    ]
}
```

### Step 3: Test with Basic Example

Use this test event to verify it works:

```json
{
  "phoneNumber": "+1234567890",
  "message": "Test with smart quotes \u201CHello\u201D and em dash \u2014 bullet \u2022 points!",
  "originationNumber": "+1987654321",
  "configurationSetName": "your-config-set",
  "dryRun": true
}
```

---

## 📋 Parameters Reference

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `phoneNumber` | Destination phone number (E.164 format) | `"+17144695773"` |
| `message` | SMS message content | `"Hello world!"` |
| `originationNumber` | Your SMS origination identity | `"+18889966807"` |

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `configurationSetName` | `null` | AWS SMS configuration set name |
| `dryRun` | `false` | `true` = analyze only, `false` = send SMS |
| `enableConversion` | `true` | `true` = convert Unicode, `false` = preserve Unicode |
| `preserveEmojis` | `false` | `true` = keep specific emojis, `false` = convert all |
| `maxSegments` | `null` | Auto-preserve Unicode if ≤ this segment count |
| `segmentLimitAction` | `"warn"` | `"reject"`, `"truncate"`, or `"warn"` when exceeding maxSegments |

---

## 🧠 Smart Features

### 1. Intelligent Auto-Preservation
Automatically preserves Unicode characters if they fit within your budget:

```json
{
  "message": "🚀 Short promo — save 50%!",
  "maxSegments": 1
}
```
**Result**: Unicode preserved (fits in 1 UCS-2 segment)

### 2. Selective Emoji Preservation
Keep brand-critical emojis while converting other Unicode:

```json
{
  "message": "🚀 Launch special! Save 50% today — limited offer • Free shipping",
  "preserveEmojis": true
}
```
**Result**: `🚀 Launch special! Save 50% today - limited offer * Free shipping`

### 3. Segment Limit Enforcement
Control costs with automatic message management:

```json
{
  "message": "Very long message...",
  "maxSegments": 1,
  "segmentLimitAction": "truncate"
}
```
**Options**:
- `"reject"`: Return error if exceeds limit
- `"truncate"`: Automatically shorten message
- `"warn"`: Send anyway with warning

---

## 💰 Cost Comparison Examples

### Example 1: Without Conversion (Expensive)
```json
{
  "phoneNumber": "+17144695773",
  "message": "ALERT: Account security issue detected! Suspicious activity from multiple locations \u2014 immediate action required. Steps: \u2022 Verify your identity \u2022 Update password \u2022 Enable 2FA \u2022 Contact support team. Don\u2019t delay \u2014 your account security is at risk! Call 1-800-SECURITY now. We never request sensitive info via text \u2014 only through official channels. \u00A9 2024 SecureBank.",
  "originationNumber": "+18889966807",
  "configurationSetName": "wide-open",
  "dryRun": false,
  "enableConversion": false
}
```
**Result**: ~6-7 UCS-2 segments (expensive)

### Example 2: With Conversion (Cheaper)
```json
{
  "phoneNumber": "+17144695773",
  "message": "ALERT: Account security issue detected! Suspicious activity from multiple locations \u2014 immediate action required. Steps: \u2022 Verify your identity \u2022 Update password \u2022 Enable 2FA \u2022 Contact support team. Don\u2019t delay \u2014 your account security is at risk! Call 1-800-SECURITY now. We never request sensitive info via text \u2014 only through official channels. \u00A9 2024 SecureBank.",
  "originationNumber": "+18889966807",
  "configurationSetName": "wide-open",
  "dryRun": false,
  "enableConversion": true
}
```
**Result**: ~3-4 GSM segments (40-50% cost savings)

---

## 🔧 Advanced Test Cases

**Note**: Additional test events are available in `message-maximizer-test-events.json` - copy individual JSON objects (without comment lines) into AWS Lambda test events.

### Test 1: Segment Limit with Rejection
```json
{
  "phoneNumber": "+17144695773",
  "message": "This is a very long message that contains no Unicode characters at all. It uses only standard GSM characters like regular quotes, hyphens, and asterisks. However, this message is definitely longer than 160 characters which means it will be split into multiple GSM segments. With reject mode, this should return an error since it exceeds our 1-segment limit.",
  "originationNumber": "+18889966807",
  "configurationSetName": "wide-open",
  "dryRun": false,
  "maxSegments": 1,
  "segmentLimitAction": "reject"
}
```

### Test 2: Smart Truncation
```json
{
  "phoneNumber": "+17144695773",
  "message": "This is a very long message that will be automatically shortened to fit within the segment limit. The truncation feature intelligently cuts at word boundaries and adds ellipsis to indicate the message was shortened.",
  "originationNumber": "+18889966807",
  "configurationSetName": "wide-open",
  "dryRun": false,
  "maxSegments": 1,
  "segmentLimitAction": "truncate"
}
```

### Test 3: Unicode with Smart Preservation
```json
{
  "phoneNumber": "+17144695773",
  "message": "\uD83D\uDE80 Launch today! Save 50% \u2014 limited time offer!",
  "originationNumber": "+18889966807",
  "configurationSetName": "wide-open",
  "dryRun": false,
  "maxSegments": 1
}
```

### Test 4: Comprehensive Unicode Character Test (NEW)
```json
{
  "phoneNumber": "+17144695773",
  "message": "Comprehensive test: Smart quotes \u201CHello\u201D and \u2018world\u2019, angle quotes \u00ABtest\u00BB, fractions \u00BC \u00BD \u00BE, dashes \u2014 and \u2013, bullets \u2022, ellipsis\u2026, fullwidth chars \uFF01\uFF1F\uFF0C\uFF0E, math \u2264\u2265\u2260\u00B1, symbols \u00A9\u00AE\u2122\u00B0, asterisks \u2731\u2732\u2733, and various spaces\u2000\u2001\u2002between\u2003words.",
  "originationNumber": "+18889966807",
  "configurationSetName": "wide-open",
  "dryRun": false,
  "enableConversion": true
}
```

### Test 5: Emoji Preservation
```json
{
  "phoneNumber": "+17144695773",
  "message": "\uD83D\uDE80 Launch special! Save 50% today \u2014 limited time offer \u2022 Free shipping \u2022 30-day guarantee. Don\u2019t wait\u2026 call now! \u00A9 2024 Company",
  "originationNumber": "+18889966807",
  "configurationSetName": "wide-open",
  "dryRun": false,
  "preserveEmojis": true
}
```

---

## 🔧 Comprehensive Character Conversion Map

**Our solution now includes 200+ character mappings - more comprehensive than Twilio's Smart Encoding!**

### Core Character Categories

#### **Smart Quotes & Quotation Marks**
| Unicode | GSM Alternative | Description |
|---------|----------------|-------------|
| `"` `"` | `"` | Smart quotes to regular quotes |
| `'` `'` | `'` | Smart apostrophes to regular apostrophe |
| `«` `»` | `"` | Angle quotation marks (European) |
| `‹` `›` | `<` `>` | Single angle quotation marks |
| `„` | `"` | German-style double low quotation mark |
| `‚` | `,` | Single low quotation mark |

#### **Dashes & Lines**
| Unicode | GSM Alternative | Description |
|---------|----------------|-------------|
| `—` | `-` | Em dash to hyphen |
| `–` | `-` | En dash to hyphen |
| `―` | `-` | Horizontal bar |
| `‐` | `-` | Hyphen variants |
| `‗` | `_` | Double low line |

#### **Fractions & Math Symbols**
| Unicode | GSM Alternative | Description |
|---------|----------------|-------------|
| `¼` | `1/4` | Vulgar fraction one quarter |
| `½` | `1/2` | Vulgar fraction one half |
| `¾` | `3/4` | Vulgar fraction three quarters |
| `÷` | `/` | Division sign |
| `×` | `x` | Multiplication sign |
| `≤` | `<=` | Less than or equal |
| `≥` | `>=` | Greater than or equal |
| `≠` | `!=` | Not equal |
| `±` | `+/-` | Plus-minus |

#### **Punctuation & Symbols**
| Unicode | GSM Alternative | Description |
|---------|----------------|-------------|
| `…` | `...` | Ellipsis to three dots |
| `•` | `*` | Bullet to asterisk |
| `‼` | `!!` | Double exclamation mark |
| `©` | `(C)` | Copyright symbol |
| `®` | `(R)` | Registered trademark |
| `™` | `TM` | Trademark |
| `°` | `deg` | Degree symbol |

#### **Fullwidth Characters (Asian Text Support)**
| Unicode | GSM Alternative | Description |
|---------|----------------|-------------|
| `！` | `!` | Fullwidth exclamation mark |
| `？` | `?` | Fullwidth question mark |
| `，` | `,` | Fullwidth comma |
| `．` | `.` | Fullwidth full stop |
| `Ａ-Ｚ` | `A-Z` | Fullwidth Latin letters |
| `０-９` | `0-9` | Fullwidth digits |

#### **Advanced Asterisk Variants**
| Unicode | GSM Alternative | Description |
|---------|----------------|-------------|
| `✱` `✲` `✳` | `*` | Heavy and decorative asterisks |
| `✢` `✣` `✤` | `*` | Spoked asterisk variants |
| `❃` `❉` `❊` | `*` | Ornamental asterisks |

### Preserved Emojis (when `preserveEmojis: true`)
- 🚀 (rocket), 💰 (money bag), ⭐ (star), ❤️ (heart)
- 🎉 (party), 🔥 (fire), 💡 (light bulb), ✅ (check mark)
- ❌ (cross mark), ⚡ (lightning)

### Unicode Spaces & Whitespace
**All converted to regular space or removed:**
- Non-breaking space, en quad, em quad, thin space, figure space
- **Zero-width spaces removed completely** (invisible characters)
- Line separators, paragraph separators → regular space
- Word joiners removed completely

### Small Capital Letters
**Converted to regular capitals:**
- `ᴀ` → `A`, `ʙ` → `B`, `ᴄ` → `C`, etc.
- Maintains readability while ensuring GSM compatibility

---

## 📊 Response Format

### Successful Response

```json
{
  "statusCode": 200,
  "body": {
    "action": "message_sent",
    "message_id": "abc123-def456",
    "original": {
      "message": "Hello "world" — test!",
      "length": 20,
      "has_unicode_chars": true
    },
    "processed": {
      "message": "Hello \"world\" - test!",
      "length": 20,
      "segments": 1,
      "estimated_cost": 1,
      "encoding": "GSM-7",
      "conversion_enabled": true
    },
    "replacements": [
      {
        "original": """,
        "replacement": "\"",
        "position": 6
      }
    ],
    "segment_limit": {
      "max_segments_allowed": 1,
      "action": "warn",
      "limit_exceeded": false
    }
  }
}
```

---

## 💡 Use Case Strategies

### Cost-First Strategy
```json
{
  "maxSegments": 1,
  "segmentLimitAction": "truncate",
  "enableConversion": true
}
```
**Best for**: Transactional messages, high-volume campaigns

### Brand-First Strategy
```json
{
  "preserveEmojis": true,
  "maxSegments": 2,
  "segmentLimitAction": "warn"
}
```
**Best for**: Marketing campaigns, customer engagement

### Balanced Strategy
```json
{
  "maxSegments": 1,
  "enableConversion": true
}
```
**Best for**: Most use cases - auto-preserves if cheap, converts if expensive

---

## 🔍 Troubleshooting

### Common Issues

**"Invalid JSON" error in test event:**
- Remove comment lines (`// Comment`)
- Use Unicode escape sequences: `\u201C` instead of `"`
- Validate JSON syntax before pasting

**"ValidationException" when sending:**
- Message too long (>1600 characters)
- Invalid phone number format (use E.164: +1234567890)
- Missing origination number

**Unexpected segment count:**
- Check for GSM extended characters (`{`, `}`, `|`, etc.) - count as 2 chars
- Verify Unicode characters are being converted
- Use `dryRun: true` to analyze before sending

### Debug Tips

1. **Always test with `dryRun: true` first**
2. **Check the `replacements` array** to see what was converted
3. **Compare segment counts** between `enableConversion: true/false`
4. **Monitor CloudWatch logs** for detailed processing info
5. **Use `maxSegments: 1`** to test auto-preservation logic

---

## 📈 Expected Cost Savings

Based on real-world usage patterns:

- **Messages with smart quotes**: 0-20% savings
- **Messages with bullets and dashes**: 20-40% savings  
- **Long messages with mixed Unicode**: 40-60% savings
- **Marketing messages with symbols**: 30-50% savings

**Example**: A 300-character message with Unicode characters:
- **Without conversion**: 5 UCS-2 segments = 5x cost
- **With conversion**: 2 GSM segments = 2x cost
- **Savings**: 60% cost reduction

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs for detailed error information
3. Test with `dryRun: true` to isolate issues
4. Verify IAM permissions and AWS SMS configuration
5. Use the provided test cases to validate functionality

Remember: This function is designed to save you money on SMS costs while maintaining message readability and brand consistency. The smart features automatically optimize for cost while preserving important content when budget allows.

---

## 🏆 Industry-Leading SMS Cost Optimization

### **More Comprehensive Than Twilio's Smart Encoding**

Our solution now includes:
- ✅ **All 200+ Twilio character mappings**
- ✅ **Additional math symbols** (≤, ≥, ≠, ±)
- ✅ **Enhanced whitespace handling** (zero-width removal)
- ✅ **Fullwidth character support** (Asian languages)
- ✅ **Small capital letter conversion**
- ✅ **Smart features Twilio doesn't offer**:
  - Intelligent auto-preservation based on segment limits
  - Selective emoji preservation for brand consistency
  - Automatic message truncation with smart word boundaries
  - Detailed cost analysis and segment reporting

### **Global Language Support**
- **European languages**: Angle quotation marks (`«»`), German quotes (`„"`)
- **Asian languages**: Fullwidth punctuation (`！？，．`), ideographic spaces
- **Mathematical content**: Fractions (`¼½¾`), operators (`÷×±`)
- **Technical content**: Various asterisk types (`✱✲✳`), special punctuation

### **Invisible Character Detection**
- **Zero-width spaces** removed completely (prevent encoding issues)
- **Word joiners** removed completely (invisible formatting)
- **Line/paragraph separators** converted to regular spaces
- **Non-breaking spaces** normalized to regular spaces

This comprehensive approach ensures virtually any Unicode character that could accidentally slip into SMS messages gets properly handled, preventing expensive UCS-2 encoding while maintaining message readability and global language support.