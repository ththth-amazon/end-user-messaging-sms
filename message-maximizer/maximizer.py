import json
import boto3
import logging
from typing import Dict, List, Tuple, Any

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize boto3 client for End User Messaging SMS
sms_client = boto3.client('pinpoint-sms-voice-v2')

# GSM 03.38 character set
GSM_BASIC_CHARS = set([
    '@', '£', '$', '¥', 'è', 'é', 'ù', 'ì', 'ò', 'Ç', '\n', 'Ø', 'ø', '\r', 'Å', 'å',
    'Δ', '_', 'Φ', 'Γ', 'Λ', 'Ω', 'Π', 'Ψ', 'Σ', 'Θ', 'Ξ', '\x1B', 'Æ', 'æ', 'ß', 'É',
    ' ', '!', '"', '#', '¤', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
    '¡', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'Ä', 'Ö', 'Ñ', 'Ü', '§',
    '¿', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'ä', 'ö', 'ñ', 'ü', 'à'
])

# GSM extended characters (require escape sequence)
GSM_EXTENDED_CHARS = set([
    '\f', '^', '{', '}', '\\', '[', '~', ']', '|', '€'
])

# Unicode characters to preserve (won't be converted even though they force UCS-2)
# These are characters you want to keep for brand/marketing reasons despite higher cost
PRESERVE_UNICODE_CHARS = set([
    '🚀',  # rocket emoji
    '💰',  # money bag emoji
    '⭐',  # star
    '❤️',  # heart
    '🎉',  # party emoji
    '🔥',  # fire emoji
    '💡',  # light bulb
    '✅',  # check mark
    '❌',  # cross mark
    '⚡',  # lightning
    # Add more characters you want to preserve here
])

# Unicode to GSM character mapping (comprehensive - includes all Twilio mappings + extras)
UNICODE_TO_GSM_MAP = {
    # Smart quotes and quotation marks
    '\u201C': '"',  # " left double quotation mark
    '\u201D': '"',  # " right double quotation mark
    '\u2018': "'",  # ' left single quotation mark
    '\u2019': "'",  # ' right single quotation mark
    '\u301E': '"',  # 〞 double prime quotation mark
    '\u00AB': '"',  # « left-pointing double angle quotation mark
    '\u00BB': '"',  # » right-pointing double angle quotation mark
    '\u2039': '<',  # ‹ single left-pointing angle quotation mark
    '\u203A': '>',  # › single right-pointing angle quotation mark
    '\u02BA': '"',  # ʺ modifier letter double prime
    '\u02EE': '"',  # ˮ modifier letter double apostrophe
    '\u201F': '"',  # ‟ double high-reversed-9 quotation mark
    '\u275D': '"',  # ❝ heavy double turned comma quotation mark ornament
    '\u275E': '"',  # ❞ heavy double comma quotation mark ornament
    '\u301D': '"',  # 〝 reversed double prime quotation mark
    '\uFF02': '"',  # ＂ fullwidth quotation mark
    '\u02BB': "'",  # ʻ modifier letter turned comma
    '\u02C8': "'",  # ˈ modifier letter vertical line
    '\u02BC': "'",  # ʼ modifier letter apostrophe
    '\u02BD': "'",  # ʽ modifier letter reversed comma
    '\u02B9': "'",  # ʹ modifier letter prime
    '\u201B': "'",  # ‛ single high-reversed-9 quotation mark
    '\uFF07': "'",  # ＇ fullwidth apostrophe
    '\u00B4': "'",  # ´ acute accent
    '\u02CA': "'",  # ˊ modifier letter acute accent
    '\u0060': "'",  # ` grave accent
    '\u02CB': "'",  # ˋ modifier letter grave accent
    '\u275B': "'",  # ❛ heavy single turned comma quotation mark ornament
    '\u275C': "'",  # ❜ heavy single comma quotation mark ornament
    '\u201A': ',',  # ‚ single low-9 quotation mark
    '\u201E': '"',  # „ double low quotation mark
    
    # Dashes and lines
    '\u2014': '-',  # — em dash
    '\u2013': '-',  # – en dash
    '\u2015': '-',  # ― horizontal bar
    '\u2010': '-',  # ‐ hyphen
    '\u2043': '-',  # ⁃ hyphen bullet
    '\u2017': '_',  # ‗ double low line
    '\u23BC': '-',  # ⎼ horizontal scan line-7
    '\u23BD': '-',  # ⎽ horizontal scan line-9
    '\uFE63': '-',  # ﹣ small hyphen-minus
    '\uFF0D': '-',  # － fullwidth hyphen-minus
    
    # Slashes and division
    '\u00F7': '/',  # ÷ division sign
    '\u29F8': '/',  # ⧸ big solidus
    '\u2044': '/',  # ⁄ fraction slash
    '\u2215': '/',  # ∕ division slash
    '\uFF0F': '/',  # ／ fullwidth solidus
    '\u29F9': '\\', # ⧹ big reverse solidus
    '\u29F5': '\\', # ⧵ reverse solidus operator
    '\uFE68': '\\', # ﹨ small reverse solidus
    '\uFF3C': '\\', # ＼ fullwidth reverse solidus
    
    # Underscores and vertical lines
    '\u0332': '_',  # ̲ combining low line
    '\uFF3F': '_',  # ＿ fullwidth low line
    '\u20D2': '|',  # ⃒ combining long vertical line overlay
    '\u20D3': '|',  # ⃓ combining short vertical line overlay
    '\u2223': '|',  # ∣ divides
    '\uFF5C': '|',  # ｜ fullwidth vertical line
    '\u23B8': '|',  # ⎸ left vertical box line
    '\u23B9': '|',  # ⎹ right vertical box line
    '\u23D0': '|',  # ⏐ vertical line extension
    '\u239C': '|',  # ⎜ left parenthesis extension
    '\u239F': '|',  # ⎟ right parenthesis extension
    
    # Fractions
    '\u00BC': '1/4',  # ¼ vulgar fraction one quarter
    '\u00BD': '1/2',  # ½ vulgar fraction one half
    '\u00BE': '3/4',  # ¾ vulgar fraction three quarters
    
    # Punctuation marks
    '\u2026': '...',  # … horizontal ellipsis
    '\u2022': '*',    # • bullet
    '\u203C': '!!',   # ‼ double exclamation mark
    '\u204E': '*',    # ⁎ low asterisk
    '\u2217': '*',    # ∗ asterisk operator
    '\u229B': '*',    # ⊛ circled asterisk operator
    '\u2722': '*',    # ✢ four teardrop-spoked asterisk
    '\u2723': '*',    # ✣ four balloon-spoked asterisk
    '\u2724': '*',    # ✤ heavy four balloon-spoked asterisk
    '\u2725': '*',    # ✥ four club-spoked asterisk
    '\u2731': '*',    # ✱ heavy asterisk
    '\u2732': '*',    # ✲ open center asterisk
    '\u2733': '*',    # ✳ eight spoked asterisk
    '\u273A': '*',    # ✺ sixteen pointed asterisk
    '\u273B': '*',    # ✻ teardrop-spoked asterisk
    '\u273C': '*',    # ✼ open center teardrop-spoked asterisk
    '\u273D': '*',    # ✽ heavy teardrop-spoked asterisk
    '\u2743': '*',    # ❃ heavy teardrop-spoked pinwheel asterisk
    '\u2749': '*',    # ❉ balloon-spoked asterisk
    '\u274A': '*',    # ❊ eight teardrop-spoked propeller asterisk
    '\u274B': '*',    # ❋ heavy eight teardrop-spoked propeller asterisk
    '\u29C6': '*',    # ⧆ squared asterisk
    '\uFE61': '*',    # ﹡ small asterisk
    '\uFF0A': '*',    # ＊ fullwidth asterisk
    
    # Fullwidth punctuation and symbols
    '\uFE6B': '@',    # ﹫ small commercial at sign
    '\uFF20': '@',    # ＠ fullwidth commercial at sign
    '\uFE69': '$',    # ﹩ small dollar sign
    '\uFF04': '$',    # ＄ fullwidth dollar sign
    '\u01C3': '!',    # ǃ Latin letter retroflex click
    '\uFE15': '!',    # ︕ presentation form for vertical exclamation mark
    '\uFE57': '!',    # ﹗ small exclamation mark
    '\uFF01': '!',    # ！ fullwidth exclamation mark
    '\uFE5F': '#',    # ﹟ small number sign
    '\uFF03': '#',    # ＃ fullwidth number sign
    '\uFE6A': '%',    # ﹪ small percent sign
    '\uFF05': '%',    # ％ fullwidth percent sign
    '\uFE60': '&',    # ﹠ small ampersand
    '\uFF06': '&',    # ＆ fullwidth ampersand
    '\uFE50': ',',    # ﹐ small comma
    '\u3001': ',',    # 、 ideographic comma
    '\uFE51': ',',    # ﹑ small ideographic comma
    '\uFF0C': ',',    # ， fullwidth comma
    '\uFF64': ',',    # ､ halfwidth ideographic comma
    '\u3002': '.',    # 。 ideographic full stop
    '\uFE52': '.',    # ﹒ small full stop
    '\uFF0E': '.',    # ． fullwidth full stop
    '\uFF61': '.',    # ｡ halfwidth ideographic full stop
    '\u02D0': ':',    # ː modifier letter triangular colon
    '\u02F8': ':',    # ˸ modifier letter raised colon
    '\u2982': ':',    # ⦂ z notation type colon
    '\uA789': ':',    # ꞉ modifier letter colon
    '\uFE13': ':',    # ︓ presentation form for vertical colon
    '\uFF1A': ':',    # ： fullwidth colon
    '\u204F': ';',    # ⁏ reversed semicolon
    '\uFE14': ';',    # ︔ presentation form for vertical semicolon
    '\uFE54': ';',    # ﹔ small semicolon
    '\uFF1B': ';',    # ； fullwidth semicolon
    '\uFE64': '<',    # ﹤ small less-than sign
    '\uFF1C': '<',    # ＜ fullwidth less-than sign
    '\uFE65': '>',    # ﹥ small greater-than sign
    '\uFF1E': '>',    # ＞ fullwidth greater-than sign
    '\uFE16': '?',    # ︖ presentation form for vertical question mark
    '\uFE56': '?',    # ﹖ small question mark
    '\uFF1F': '?',    # ？ fullwidth question mark
    
    # Parentheses and brackets
    '\u2768': '(',    # ❨ medium left parenthesis ornament
    '\u276A': '(',    # ❪ medium flattened left parenthesis ornament
    '\uFE59': '(',    # ﹙ small left parenthesis
    '\uFF08': '(',    # （ fullwidth left parenthesis
    '\u27EE': '(',    # ⟮ mathematical left flattened parenthesis
    '\u2985': '(',    # ⦅ left white parenthesis
    '\u2769': ')',    # ❩ medium right parenthesis ornament
    '\u276B': ')',    # ❫ medium flattened right parenthesis ornament
    '\uFE5A': ')',    # ﹚ small right parenthesis
    '\uFF09': ')',    # ） fullwidth right parenthesis
    '\u27EF': ')',    # ⟯ mathematical right flattened parenthesis
    '\u2986': ')',    # ⦆ right white parenthesis
    '\u2774': '{',    # ❴ medium left curly bracket ornament
    '\uFE5B': '{',    # ﹛ small left curly bracket
    '\uFF5B': '{',    # ｛ fullwidth left curly bracket
    '\u2775': '}',    # ❵ medium right curly bracket ornament
    '\uFE5C': '}',    # ﹜ small right curly bracket
    '\uFF5D': '}',    # ｝ fullwidth right curly bracket
    '\uFF3B': '[',    # ［ fullwidth left square bracket
    '\uFF3D': ']',    # ］ fullwidth right square bracket
    
    # Plus and other operators
    '\u02D6': '+',    # ˖ modifier letter plus sign
    '\uFE62': '+',    # ﹢ small plus sign
    '\uFF0B': '+',    # ＋ fullwidth plus sign
    
    # Circumflex and tilde
    '\u02C6': '^',    # ˆ modifier letter circumflex accent
    '\u0302': '^',    # ̂ combining circumflex accent
    '\uFF3E': '^',    # ＾ fullwidth circumflex accent
    '\u1DCD': '^',    # ᷍ combining double circumflex above
    '\u02DC': '~',    # ˜ small tilde
    '\u02F7': '~',    # ˷ modifier letter low tilde
    '\u0303': '~',    # ̃ combining tilde
    '\u0330': '~',    # ̰ combining tilde below
    '\u0334': '~',    # ̴ combining tilde overlay
    '\u223C': '~',    # ∼ tilde operator
    '\uFF5E': '~',    # ～ fullwidth tilde
    
    # Fullwidth digits
    '\uFF10': '0',    # ０ fullwidth digit zero
    '\uFF11': '1',    # １ fullwidth digit one
    '\uFF12': '2',    # ２ fullwidth digit two
    '\uFF13': '3',    # ３ fullwidth digit three
    '\uFF14': '4',    # ４ fullwidth digit four
    '\uFF15': '5',    # ５ fullwidth digit five
    '\uFF16': '6',    # ６ fullwidth digit six
    '\uFF17': '7',    # ７ fullwidth digit seven
    '\uFF18': '8',    # ８ fullwidth digit eight
    '\uFF19': '9',    # ９ fullwidth digit nine
    
    # Fullwidth letters (uppercase)
    '\uFF21': 'A',    # Ａ fullwidth Latin capital letter a
    '\uFF22': 'B',    # Ｂ fullwidth Latin capital letter b
    '\uFF23': 'C',    # Ｃ fullwidth Latin capital letter c
    '\uFF24': 'D',    # Ｄ fullwidth Latin capital letter d
    '\uFF25': 'E',    # Ｅ fullwidth Latin capital letter e
    '\uFF26': 'F',    # Ｆ fullwidth Latin capital letter f
    '\uFF27': 'G',    # Ｇ fullwidth Latin capital letter g
    '\uFF28': 'H',    # Ｈ fullwidth Latin capital letter h
    '\uFF29': 'I',    # Ｉ fullwidth Latin capital letter i
    '\uFF2A': 'J',    # Ｊ fullwidth Latin capital letter j
    '\uFF2B': 'K',    # Ｋ fullwidth Latin capital letter k
    '\uFF2C': 'L',    # Ｌ fullwidth Latin capital letter l
    '\uFF2D': 'M',    # Ｍ fullwidth Latin capital letter m
    '\uFF2E': 'N',    # Ｎ fullwidth Latin capital letter n
    '\uFF2F': 'O',    # Ｏ fullwidth Latin capital letter o
    '\uFF30': 'P',    # Ｐ fullwidth Latin capital letter p
    '\uFF31': 'Q',    # Ｑ fullwidth Latin capital letter q
    '\uFF32': 'R',    # Ｒ fullwidth Latin capital letter r
    '\uFF33': 'S',    # Ｓ fullwidth Latin capital letter s
    '\uFF34': 'T',    # Ｔ fullwidth Latin capital letter t
    '\uFF35': 'U',    # Ｕ fullwidth Latin capital letter u
    '\uFF36': 'V',    # Ｖ fullwidth Latin capital letter v
    '\uFF37': 'W',    # Ｗ fullwidth Latin capital letter w
    '\uFF38': 'X',    # Ｘ fullwidth Latin capital letter x
    '\uFF39': 'Y',    # Ｙ fullwidth Latin capital letter y
    '\uFF3A': 'Z',    # Ｚ fullwidth Latin capital letter z
    
    # Small capital letters (convert to regular capitals)
    '\u1D00': 'A',    # ᴀ Latin letter small capital a
    '\u0299': 'B',    # ʙ Latin letter small capital b
    '\u1D04': 'C',    # ᴄ Latin letter small capital c
    '\u1D05': 'D',    # ᴅ Latin letter small capital d
    '\u1D07': 'E',    # ᴇ Latin letter small capital e
    '\uA730': 'F',    # ꜰ Latin letter small capital f
    '\u0262': 'G',    # ɢ Latin letter small capital g
    '\u029C': 'H',    # ʜ Latin letter small capital h
    '\u026A': 'I',    # ɪ Latin letter small capital i
    '\u1D0A': 'J',    # ᴊ Latin letter small capital j
    '\u1D0B': 'K',    # ᴋ Latin letter small capital k
    '\u029F': 'L',    # ʟ Latin letter small capital l
    '\u1D0D': 'M',    # ᴍ Latin letter small capital m
    '\u0274': 'N',    # ɴ Latin letter small capital n
    '\u1D0F': 'O',    # ᴏ Latin letter small capital o
    '\u1D18': 'P',    # ᴘ Latin letter small capital p
    '\u0280': 'R',    # ʀ Latin letter small capital r
    '\uA731': 'S',    # ꜱ Latin letter small capital s
    '\u1D1B': 'T',    # ᴛ Latin letter small capital t
    '\u1D1C': 'U',    # ᴜ Latin letter small capital u
    '\u1D20': 'V',    # ᴠ Latin letter small capital v
    '\u1D21': 'W',    # ᴡ Latin letter small capital w
    '\u028F': 'Y',    # ʏ Latin letter small capital y
    '\u1D22': 'Z',    # ᴢ Latin letter small capital z
    
    # Spaces and whitespace (comprehensive)
    '\u00A0': ' ',    # non-breaking space
    '\u2000': ' ',    # en quad
    '\u2001': ' ',    # em quad
    '\u2002': ' ',    # en space
    '\u2003': ' ',    # em space
    '\u2004': ' ',    # three-per-em space
    '\u2005': ' ',    # four-per-em space
    '\u2006': ' ',    # six-per-em space
    '\u2007': ' ',    # figure space
    '\u2008': ' ',    # punctuation space
    '\u2009': ' ',    # thin space
    '\u200A': ' ',    # hair space
    '\u200B': '',     # zero width space (remove completely)
    '\u202F': ' ',    # narrow no-break space
    '\u205F': ' ',    # medium mathematical space
    '\u2028': ' ',    # line separator
    '\u2029': ' ',    # paragraph separator
    '\u2060': '',     # word joiner (remove completely)
    '\u3000': ' ',    # ideographic space
    '\uFEFF': '',     # zero width no-break space (remove completely)
    
    # Additional symbols (our extras beyond Twilio)
    '\u2122': 'TM',   # ™ trademark
    '\u00A9': '(C)',  # © copyright
    '\u00AE': '(R)',  # ® registered
    '\u00B0': 'deg',  # ° degree symbol
    '\u2264': '<=',   # ≤ less than or equal
    '\u2265': '>=',   # ≥ greater than or equal
    '\u2260': '!=',   # ≠ not equal
    '\u00B1': '+/-'   # ± plus-minus
}

def is_gsm_character(char: str) -> bool:
    """Check if a character is valid in GSM 03.38 character set."""
    return char in GSM_BASIC_CHARS or char in GSM_EXTENDED_CHARS

def truncate_message_to_segments(message: str, max_segments: int) -> str:
    """Truncate message to fit within specified segment count."""
    if max_segments == 1:
        max_chars = 160
    else:
        # First segment: 160 chars, subsequent segments: 153 chars each
        max_chars = 160 + (max_segments - 1) * 153
    
    if len(message) <= max_chars:
        return message
    
    # Smart truncation at word boundary
    truncated = message[:max_chars-3]  # Leave room for "..."
    
    # Find last space to avoid cutting words
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.8:  # Only use word boundary if it's not too far back
        truncated = truncated[:last_space]
    
    return truncated + "..."

def convert_to_gsm(message: str, preserve_emojis: bool = False, max_segments: int = None) -> Dict[str, Any]:
    """Convert Unicode characters to GSM-compatible alternatives."""
    
    # If max_segments is specified, first check if we can preserve all Unicode
    if max_segments is not None:
        # Calculate segments if we keep all Unicode characters (UCS-2 encoding)
        original_segments, _ = calculate_segments(message)
        
        if original_segments <= max_segments:
            # We can afford to keep all Unicode characters
            return {
                'converted_message': message,
                'replacements': [{
                    'original': 'ALL_UNICODE',
                    'replacement': 'PRESERVED',
                    'position': -1,
                    'preserved': True,
                    'note': f'All Unicode preserved - message fits in {original_segments} segment(s) (≤ {max_segments} limit)'
                }],
                'original_length': len(message),
                'converted_length': len(message),
                'auto_preserved': True,
                'segments_if_preserved': original_segments,
                'max_segments_allowed': max_segments
            }
    
    converted_message = ""
    replacements = []
    
    for i, char in enumerate(message):
        if is_gsm_character(char):
            converted_message += char
        elif preserve_emojis and char in PRESERVE_UNICODE_CHARS:
            # Keep this Unicode character even though it forces UCS-2 encoding
            converted_message += char
            replacements.append({
                'original': char,
                'replacement': char,
                'position': i,
                'preserved': True,
                'note': 'Preserved Unicode character (forces UCS-2 encoding)'
            })
        elif char in UNICODE_TO_GSM_MAP:
            replacement = UNICODE_TO_GSM_MAP[char]
            converted_message += replacement
            replacements.append({
                'original': char,
                'replacement': replacement,
                'position': i
            })
        else:
            # For unmapped Unicode characters, try to find a reasonable ASCII alternative
            import unicodedata
            try:
                normalized = unicodedata.normalize('NFD', char)
                ascii_char = ''.join(c for c in normalized if not unicodedata.combining(c))
                if ascii_char != char and is_gsm_character(ascii_char):
                    converted_message += ascii_char
                    replacements.append({
                        'original': char,
                        'replacement': ascii_char,
                        'position': i
                    })
                else:
                    # If no mapping found, replace with '?'
                    converted_message += '?'
                    replacements.append({
                        'original': char,
                        'replacement': '?',
                        'position': i
                    })
            except:
                # If normalization fails, replace with '?'
                converted_message += '?'
                replacements.append({
                    'original': char,
                    'replacement': '?',
                    'position': i
                })
    
    result = {
        'converted_message': converted_message,
        'replacements': replacements,
        'original_length': len(message),
        'converted_length': len(converted_message),
        'auto_preserved': False
    }
    
    # If max_segments was specified, add analysis info
    if max_segments is not None:
        converted_segments, _ = calculate_segments(converted_message)
        original_segments, _ = calculate_segments(message)
        result.update({
            'segments_if_preserved': original_segments,
            'segments_after_conversion': converted_segments,
            'max_segments_allowed': max_segments,
            'conversion_reason': f'Conversion applied - original would be {original_segments} segments (> {max_segments} limit)'
        })
    
    return result

def calculate_segments(message: str) -> tuple:
    """Calculate SMS segment count and determine encoding type."""
    # Check if message contains any Unicode characters (including preserved ones)
    has_unicode = False
    try:
        message.encode('ascii')
    except UnicodeEncodeError:
        has_unicode = True
    
    if has_unicode:
        # UCS-2 encoding (Unicode)
        length = len(message)
        if length <= 70:
            segments = 1
        else:
            segments = (length + 66) // 67  # 67 chars per segment for multi-part UCS-2
        encoding = 'UCS-2 (Unicode)'
    else:
        # GSM-7 encoding
        length = 0
        for char in message:
            if char in GSM_EXTENDED_CHARS:
                length += 2  # Extended characters require escape sequence
            else:
                length += 1
        
        if length <= 160:
            segments = 1
        else:
            segments = (length + 152) // 153  # 153 chars per segment for multi-part GSM
        encoding = 'GSM-7'
    
    return segments, encoding

def lambda_handler(event, context):
    """AWS Lambda handler function."""
    logger.info(f'Lambda function invoked with event: {json.dumps(event)}')
    
    try:
        # Handle both direct invocation and API Gateway events
        if 'body' in event and event['body']:
            request_body = json.loads(event['body'])
        else:
            request_body = event
        
        # Extract parameters
        phone_number = request_body.get('phoneNumber')
        message = request_body.get('message')
        origination_number = request_body.get('originationNumber')
        configuration_set_name = request_body.get('configurationSetName')
        dry_run = request_body.get('dryRun', False)
        enable_conversion = request_body.get('enableConversion', True)
        preserve_emojis = request_body.get('preserveEmojis', False)
        max_segments = request_body.get('maxSegments', None)  # Auto-preserve if under this limit
        segment_limit_action = request_body.get('segmentLimitAction', 'warn')  # 'reject', 'truncate', 'warn'
        
        # Validate required parameters
        if not phone_number or not message:
            error_response = {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'phoneNumber and message are required parameters',
                    'action': 'validation_error'
                })
            }
            logger.error(f'Validation error: {error_response["body"]}')
            return error_response
        
        logger.info(f'Processing message for {phone_number}: "{message}"')
        logger.info(f'Conversion enabled: {enable_conversion}')
        
        if not enable_conversion:
            # Skip conversion - use original message and calculate UCS-2 segments
            conversion = {
                'converted_message': message,
                'replacements': [],
                'original_length': len(message),
                'converted_length': len(message)
            }
            
            # Check if message actually contains Unicode characters
            has_unicode = False
            unicode_chars = []
            try:
                message.encode('ascii')
            except UnicodeEncodeError:
                has_unicode = True
                for i, char in enumerate(message):
                    if ord(char) > 127:
                        unicode_chars.append({'char': char, 'code': ord(char), 'position': i})
            
            # Calculate segments based on encoding
            message_length = len(message)
            if has_unicode:
                # UCS-2 encoding limits
                if message_length <= 70:
                    segments = 1
                else:
                    # Multi-part UCS-2 messages have 67 characters per segment
                    segments = (message_length + 66) // 67
                encoding_type = 'UCS-2 (Unicode)'
            else:
                # GSM-7 encoding limits (even without conversion)
                if message_length <= 160:
                    segments = 1
                else:
                    segments = (message_length + 152) // 153
                encoding_type = 'GSM-7 (ASCII only)'
            
            logger.info(f'Unicode detection: {has_unicode}, Unicode chars: {unicode_chars}')
        else:
            # Convert Unicode characters to GSM alternatives
            conversion = convert_to_gsm(message, preserve_emojis, max_segments)
            segments, encoding_type = calculate_segments(conversion['converted_message'])
            
            # Handle segment limit enforcement if maxSegments is specified
            if max_segments is not None and segments > max_segments:
                if segment_limit_action == 'reject':
                    error_response = {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': f'Message exceeds segment limit: {segments} segments > {max_segments} allowed',
                            'action': 'segment_limit_exceeded',
                            'current_segments': segments,
                            'max_segments_allowed': max_segments,
                            'message_length': len(conversion['converted_message']),
                            'encoding': encoding_type
                        })
                    }
                    logger.error(f'Message rejected - segment limit exceeded: {error_response["body"]}')
                    return error_response
                
                elif segment_limit_action == 'truncate':
                    # Truncate the converted message to fit segment limit
                    original_message = conversion['converted_message']
                    truncated_message = truncate_message_to_segments(original_message, max_segments)
                    
                    # Recalculate segments after truncation
                    new_segments, new_encoding = calculate_segments(truncated_message)
                    
                    # Update conversion result
                    conversion['converted_message'] = truncated_message
                    conversion['converted_length'] = len(truncated_message)
                    conversion['truncated'] = True
                    conversion['truncated_from'] = len(original_message)
                    conversion['truncated_to'] = len(truncated_message)
                    
                    segments = new_segments
                    encoding_type = new_encoding
                    
                    logger.info(f'Message truncated from {len(original_message)} to {len(truncated_message)} characters to fit {max_segments} segments')
                
                # For 'warn' action, we just continue and add warning to response
        
        logger.info(f'Message processing complete. Original length: {conversion["original_length"]}, '
                   f'Final length: {conversion["converted_length"]}, Segments: {segments}, Encoding: {encoding_type}')
        
        analysis_result = {
            'original': {
                'message': message,
                'length': conversion['original_length'],
                'has_unicode_chars': len(conversion['replacements']) > 0
            },
            'processed': {
                'message': conversion['converted_message'],
                'length': conversion['converted_length'],
                'segments': segments,
                'estimated_cost': segments,
                'encoding': encoding_type,
                'conversion_enabled': enable_conversion
            },
            'replacements': conversion['replacements']
        }
        
        # Add segment limit information if specified
        if max_segments is not None:
            analysis_result['segment_limit'] = {
                'max_segments_allowed': max_segments,
                'action': segment_limit_action,
                'limit_exceeded': segments > max_segments
            }
            
            # Add truncation info if message was truncated
            if conversion.get('truncated'):
                analysis_result['segment_limit']['truncated'] = True
                analysis_result['segment_limit']['original_length'] = conversion['truncated_from']
                analysis_result['segment_limit']['truncated_length'] = conversion['truncated_to']
            
            # Add warning if limit exceeded but action is 'warn'
            if segments > max_segments and segment_limit_action == 'warn':
                analysis_result['segment_limit']['warning'] = f'Message sent as {segments} segments (exceeds {max_segments} preference)'
        
        # If dry run mode, return analysis without sending SMS
        if dry_run:
            logger.info('Dry run mode - returning analysis only')
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'action': 'analysis_only',
                    **analysis_result
                })
            }
        
        # Validate SMS sending parameters
        if not origination_number:
            error_response = {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'originationNumber is required for sending SMS',
                    'action': 'validation_error'
                })
            }
            logger.error(f'SMS validation error: {error_response["body"]}')
            return error_response
        
        # Prepare SMS parameters
        sms_params = {
            'DestinationPhoneNumber': phone_number,
            'MessageBody': conversion['converted_message'],
            'OriginationIdentity': origination_number
        }
        
        # Add configuration set if provided
        if configuration_set_name:
            sms_params['ConfigurationSetName'] = configuration_set_name
        
        # Validate message length before sending
        message_to_send = conversion['converted_message']
        if len(message_to_send) > 1600:  # AWS SMS limit is typically 1600 chars
            error_response = {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Message too long: {len(message_to_send)} characters. AWS SMS limit is 1600 characters.',
                    'action': 'validation_error',
                    'message_length': len(message_to_send),
                    'segments': segments
                })
            }
            logger.error(f'Message too long: {error_response["body"]}')
            return error_response
        
        logger.info(f'Sending SMS via AWS End User Messaging... Message length: {len(message_to_send)} chars')
        
        # Send the SMS (using the processed message - converted or original)
        send_result = sms_client.send_text_message(**sms_params)
        
        logger.info(f'SMS sent successfully: {send_result["MessageId"]}')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'action': 'message_sent',
                'message_id': send_result['MessageId'],
                **analysis_result
            })
        }
        
    except Exception as error:
        logger.error(f'Lambda execution error: {str(error)}', exc_info=True)
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(error),
                'error_type': type(error).__name__,
                'action': 'error'
            })
        }
