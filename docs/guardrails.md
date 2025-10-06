# Input Guardrails (PII Detection)

## Overview

The Input Guardrails system is a security layer designed to prevent the processing of tickets containing Personally Identifiable Information (PII). This system acts as the **first step** in the ticket resolution workflow, scanning all incoming tickets before they proceed to downstream processing.

### Purpose

- **Data Protection**: Prevent PII from entering the system and potentially being logged, stored, or processed
- **Compliance**: Help meet data privacy regulations (GDPR, CCPA, HIPAA, etc.)
- **Security**: Reduce the risk of data breaches and unauthorized exposure of sensitive information
- **Early Detection**: Catch PII at the entry point before it propagates through the system

## Architecture

### Workflow Position

```
START
  ↓
┌─────────────────────────┐
│  Input Guardrails       │  ← First step (NEW)
└─────────────────────────┘
  ↓
  ├─ PII Detected? → END (create error.json)
  ↓
  └─ No PII → Query Refinement Check → [rest of workflow...]
```

The Input Guardrails node is positioned as the **first node** after START in the LangGraph workflow, ensuring that no ticket with PII proceeds to query refinement, reasoning, or execution steps.

### Components

The guardrails system consists of four main components:

1. **Data Models** (`models/data_models.py`)
   - `PIIDetectionItem`: Individual PII detection record
   - `PIIDetectionResult`: Complete detection scan result
   - `GuardrailError`: Error object created when PII is found

2. **PII Detector** (`guardrails/pii_detector.py`)
   - Core detection logic using regex patterns
   - Pattern matching for emails, SSNs, phone numbers, credit cards, etc.

3. **Configuration** (`guardrails/config.py`)
   - Regex patterns for different PII types
   - Enable/disable specific checks
   - Behavior settings

4. **Graph Integration** (`graph/nodes.py`, `graph/supervisor_graph.py`)
   - `pii_guardrail_check()` node function
   - `route_after_pii_check()` router function
   - Graph edges and conditional routing

## How It Works

### 1. Detection Process

When a ticket enters the system:

1. **Session Creation**: A unique session folder is created with format `MMDDYYYY_HHMM_UUID`
2. **Ticket Extraction**: The ticket description is extracted from the input messages
3. **PII Scanning**: The `PIIDetector` scans the ticket text using regex patterns
4. **Decision**: Based on detection results, the workflow either:
   - **PII Found**: Creates `error.json`, terminates workflow (routes to END)
   - **No PII**: Proceeds to Query Refinement Check

### 2. PII Types Detected

The system currently detects the following PII types:

| PII Type | Pattern | Example |
|----------|---------|---------|
| Email | RFC 5322 simplified | `john.doe@example.com` |
| SSN | XXX-XX-XXXX | `123-45-6789` |
| Phone | US format with variations | `(555) 123-4567`, `555-123-4567` |
| Credit Card | 13-19 digits with separators | `1234-5678-9012-3456` |
| IP Address | IPv4 | `192.168.1.1` |

### 3. Error Handling

When PII is detected, the system:

1. **Creates Error Object**: A `GuardrailError` instance with:
   - Error type: `"PII_DETECTED"`
   - Error message describing the issue
   - Full detection results including PII types and counts
   - Session ID and timestamp

2. **Saves to Session Folder**: `error.json` file in session directory
   ```
   sessions/10052025_1430_a1b2/error.json
   ```

3. **Terminates Workflow**: Routes directly to END, skipping all processing steps

4. **Logs to Console**: Displays warning with session ID and PII types found

### 4. Session Management

The guardrail check creates the session folder and stores the session ID in the workflow state. This ensures:

- Consistent session tracking across all workflow steps
- Error output is saved in the correct session folder
- Downstream nodes can reuse the session ID (no duplicate folders)

## Implementation Details

### Code Structure

```
RCS-Standalone-Code/
├── guardrails/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # PII patterns and settings
│   └── pii_detector.py          # Core detection logic
├── models/
│   └── data_models.py           # PII data models + state updates
├── graph/
│   ├── nodes.py                 # pii_guardrail_check() + router
│   └── supervisor_graph.py      # Graph structure updates
└── sessions/
    └── MMDDYYYY_HHMM_UUID/
        └── error.json           # Created when PII detected
```

### Key Functions

#### `pii_guardrail_check(state: SolutionState)`
**Location**: `graph/nodes.py:65`

The main node function that executes PII detection:

```python
def pii_guardrail_check(state: SolutionState):
    """
    PII Guardrail Check - First step in the workflow

    Scans incoming ticket for PII.
    If PII detected: creates error.json and routes to END.
    If no PII: proceeds to Query Refinement Check.
    """
    # 1. Create session folder
    session_id, session_path = create_session_folder()

    # 2. Extract ticket description
    ticket_description = extract_from_messages_or_sample(state)

    # 3. Run PII detection
    pii_detector = PIIDetector()
    pii_result = pii_detector.detect(ticket_description, session_id)

    # 4. Handle results
    if pii_result.pii_found:
        # Create error and save to session
        guardrail_error = GuardrailError(...)
        save_error_json(guardrail_error, session_path)
        return state_with_error
    else:
        # No PII - proceed
        return state_with_clean_result
```

**Key Responsibilities**:
- Session folder creation (first node to do this)
- Ticket extraction from state or sample data
- PII detection execution
- Error handling and file creation
- State updates for routing

#### `route_after_pii_check(state: SolutionState)`
**Location**: `graph/nodes.py:353`

Router function for conditional graph edges:

```python
def route_after_pii_check(state: SolutionState) -> Literal["Query Refinement Check", END]:
    """
    Routes to END if PII detected.
    Routes to Query Refinement Check if no PII.
    """
    if "guardrail_error" in state and state["guardrail_error"]:
        return END
    return "Query Refinement Check"
```

**Key Responsibilities**:
- Check state for guardrail error
- Return appropriate next node or END

#### `PIIDetector.detect(text: str, session_id: str)`
**Location**: `guardrails/pii_detector.py:44`

Core detection logic:

```python
def detect(self, text: str, session_id: str = "unknown") -> PIIDetectionResult:
    """
    Detect PII in the given text.

    Returns:
        PIIDetectionResult containing:
        - pii_found: bool
        - pii_types: List[str]
        - pii_count: int
        - detection_details: List[PIIDetectionItem]
        - ticket_excerpt: str (first 150 chars)
        - session_id: str
        - timestamp: str
    """
```

**Key Features**:
- Uses compiled regex patterns for performance
- Finds all matches (not just first)
- Tracks position and type of each PII item
- Configurable pattern inclusion in results (security)

### Data Flow

```
Input Ticket
    ↓
pii_guardrail_check(state)
    ↓
PIIDetector.detect(text)
    ↓
regex pattern matching
    ↓
PIIDetectionResult
    ↓
Decision:
    ├─ PII Found → GuardrailError → error.json → END
    └─ No PII → state update → Query Refinement Check
```

### State Management

The system uses LangGraph's `SolutionState` TypedDict with two new fields:

```python
class SolutionState(TypedDict, total=False):
    # ... existing fields ...
    pii_detection_result: Optional[PIIDetectionResult]  # Always present after PII check
    guardrail_error: Optional[GuardrailError]           # Only present if PII found
```

**State Flow**:
1. **PII Check**: Adds `pii_detection_result` to state (always)
2. **PII Detected**: Adds `guardrail_error` to state (conditional)
3. **Router**: Checks for `guardrail_error` existence
4. **Downstream Nodes**: Can access `pii_detection_result.session_id` for reuse

## Configuration Guide

### Enabling/Disabling PII Checks

Edit `guardrails/config.py`:

```python
# Disable specific PII checks
ENABLED_PII_CHECKS = [
    "EMAIL",
    "SSN",
    # "PHONE",        # Commented out = disabled
    "CREDIT_CARD",
    "IP_ADDRESS"
]
```

### Adding Custom PII Patterns

**Method 1: Static Configuration** (Recommended)

Edit `guardrails/config.py`:

```python
PII_PATTERNS = {
    "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b',

    # Add custom pattern
    "PASSPORT": r'\b[A-Z]{1,2}\d{6,9}\b',
}

# Enable the new check
ENABLED_PII_CHECKS = [
    "EMAIL",
    "SSN",
    "PASSPORT",  # NEW
]
```

**Method 2: Runtime Addition**

```python
from guardrails import PIIDetector

detector = PIIDetector()
detector.add_pattern("PASSPORT", r'\b[A-Z]{1,2}\d{6,9}\b')
result = detector.detect(ticket_text)
```

### Adjusting Behavior Settings

Edit `guardrails/config.py`:

```python
GUARDRAIL_SETTINGS = {
    # Create error.json when PII is detected
    "create_error_file": True,

    # Maximum length of ticket excerpt in error details
    "ticket_excerpt_length": 150,

    # Include matched PII patterns in error output
    # WARNING: Set to False in production to avoid logging actual PII
    "include_matched_patterns": False,  # Changed to False for security
}
```

## Usage Examples

### Example 1: Normal Ticket (No PII)

**Input**:
```
"User cannot access the dashboard. Error message: 'Access Denied'"
```

**Behavior**:
- ✓ PII check passes
- ✓ Proceeds to Query Refinement Check
- ✓ Normal workflow continues
- ✓ Session folder created with only normal output files

**Console Output**:
```
✓ Input Guardrails Passed - No PII detected
Session: 10052025_1430_a1b2
```

### Example 2: Ticket with PII

**Input**:
```
"User john.doe@example.com cannot login. Please call 555-123-4567."
```

**Behavior**:
- ⚠️ PII detected: EMAIL, PHONE
- ⚠️ Workflow terminates at guardrail
- ⚠️ `error.json` created in session folder
- ⚠️ No downstream processing occurs

**Console Output**:
```
⚠️  PII DETECTED - Workflow terminated
Session: 10052025_1430_a1b2
PII Types Found: EMAIL, PHONE
Error details saved to: sessions/10052025_1430_a1b2/error.json
```

**error.json Content**:
```json
{
  "error_type": "PII_DETECTED",
  "error_message": "Ticket contains personally identifiable information (PII) and cannot be processed. Found 2 PII item(s) of types: EMAIL, PHONE",
  "detection_result": {
    "pii_found": true,
    "pii_types": ["EMAIL", "PHONE"],
    "pii_count": 2,
    "detection_details": [
      {
        "pii_type": "EMAIL",
        "pattern_matched": "john.doe@example.com",
        "location": 5
      },
      {
        "pii_type": "PHONE",
        "pattern_matched": "555-123-4567",
        "location": 50
      }
    ],
    "ticket_excerpt": "User john.doe@example.com cannot login. Please call 555-123-4567.",
    "session_id": "10052025_1430_a1b2",
    "timestamp": "2025-10-05T14:30:15.123456"
  },
  "session_id": "10052025_1430_a1b2",
  "timestamp": "2025-10-05T14:30:15.123456"
}
```

### Example 3: Programmatic Usage

```python
from guardrails import PIIDetector

# Create detector
detector = PIIDetector()

# Scan text
ticket_text = "Contact support at support@company.com"
result = detector.detect(ticket_text, session_id="test_123")

# Check results
if result.pii_found:
    print(f"Found {result.pii_count} PII items")
    print(f"Types: {', '.join(result.pii_types)}")
    for item in result.detection_details:
        print(f"  - {item.pii_type} at position {item.location}")
else:
    print("No PII detected")
```

## Testing Guide

### Unit Testing the PIIDetector

Create test cases for the detector:

```python
import pytest
from guardrails import PIIDetector

def test_email_detection():
    detector = PIIDetector()
    result = detector.detect("Contact me at test@example.com")

    assert result.pii_found is True
    assert "EMAIL" in result.pii_types
    assert result.pii_count >= 1

def test_no_pii():
    detector = PIIDetector()
    result = detector.detect("This is a clean ticket")

    assert result.pii_found is False
    assert result.pii_count == 0

def test_multiple_pii_types():
    detector = PIIDetector()
    text = "Call 555-1234 or email test@example.com"
    result = detector.detect(text)

    assert result.pii_found is True
    assert "EMAIL" in result.pii_types
    assert "PHONE" in result.pii_types
```

### Integration Testing

Test the full workflow with PII:

```bash
# Create test ticket with PII
python main.py "Process this ticket: User email is test@example.com"

# Verify:
# 1. Workflow terminates early
# 2. error.json created in session folder
# 3. Console shows PII detection warning
```

Test the workflow without PII:

```bash
# Create clean ticket
python main.py "Process this ticket: Dashboard is not loading"

# Verify:
# 1. Workflow completes normally
# 2. No error.json created
# 3. Normal session outputs generated
```

### Test Data

Create test tickets in `data/test_tickets/`:

**pii_email_phone.json**:
```json
{
  "ticket_description": "User john.doe@example.com reports login failure. Contact: 555-123-4567"
}
```

**pii_ssn_credit.json**:
```json
{
  "ticket_description": "SSN 123-45-6789 and card 1234-5678-9012-3456 found in logs"
}
```

**clean_ticket.json**:
```json
{
  "ticket_description": "Application crashes when clicking submit button"
}
```

## Best Practices

### 1. Security Considerations

**DO**:
- Set `include_matched_patterns: False` in production to avoid logging actual PII
- Regularly review and update PII patterns
- Limit access to session folders containing error.json files
- Consider encrypting session folder contents
- Audit who can view error.json files

**DON'T**:
- Don't log the actual PII values in production environments
- Don't send error.json contents over unencrypted channels
- Don't store PII detection results indefinitely
- Don't disable all PII checks without risk assessment

### 2. Pattern Management

**Start Conservative**:
- Begin with high-confidence patterns (email, SSN, credit cards)
- Add new patterns gradually after testing
- Monitor false positive rates

**Pattern Quality**:
- Use well-tested regex patterns from established libraries (Presidio, DataFog)
- Test patterns against diverse input samples
- Balance precision vs. recall based on use case

### 3. Performance Optimization

**Regex Compilation**:
- Patterns are pre-compiled in `PIIDetector.__init__()` for performance
- Reuse detector instances when scanning multiple tickets

**Pattern Efficiency**:
- Keep patterns as specific as possible
- Avoid overly broad patterns that cause excessive backtracking
- Consider pattern complexity vs. detection accuracy tradeoff

### 4. Monitoring and Maintenance

**Track Metrics**:
- Count of PII detections per day/week
- Most common PII types detected
- False positive reports from users

**Regular Reviews**:
- Review error.json files to identify patterns
- Update detection rules based on new PII types
- Audit effectiveness of current patterns

## Troubleshooting

### Issue: False Positives

**Symptom**: Clean tickets are flagged as containing PII

**Causes**:
- Overly broad regex patterns
- Test data patterns matching real PII patterns
- Phone-like numbers (e.g., error codes, IDs)

**Solutions**:
1. Refine regex patterns to be more specific
2. Add whitelist patterns for known false positives
3. Adjust pattern confidence thresholds
4. Consider context-aware detection (future enhancement)

### Issue: False Negatives

**Symptom**: Tickets with PII pass through the guardrail

**Causes**:
- PII format not covered by current patterns
- International PII formats (non-US)
- Obfuscated or formatted PII

**Solutions**:
1. Add new patterns for uncovered PII types
2. Implement international pattern variants
3. Add patterns for common PII obfuscation techniques
4. Consider NLP-based detection for names/addresses

### Issue: Performance Degradation

**Symptom**: Slow ticket processing at guardrail step

**Causes**:
- Complex regex patterns with backtracking
- Very long ticket descriptions
- Too many patterns enabled

**Solutions**:
1. Optimize regex patterns (avoid excessive backtracking)
2. Limit ticket description length before scanning
3. Disable unnecessary pattern checks
4. Use regex timeout mechanisms

### Issue: Session Folder Errors

**Symptom**: Cannot create error.json or session folder

**Causes**:
- Insufficient permissions
- Disk space issues
- Path configuration errors

**Solutions**:
1. Check `sessions/` folder permissions
2. Verify disk space availability
3. Check `utils/helpers.py` path configuration
4. Ensure `ensure_directory_exists()` function works correctly

## Advanced Topics

### Custom PII Detectors

Create specialized detectors for domain-specific PII:

```python
from guardrails.pii_detector import PIIDetector

class MedicalPIIDetector(PIIDetector):
    def __init__(self):
        medical_patterns = {
            "MEDICAL_RECORD": r'\bMRN[-\s]?\d{6,10}\b',
            "PATIENT_ID": r'\bPID[-\s]?\d{6,10}\b',
            "INSURANCE_ID": r'\b[A-Z]{2}\d{8,12}\b'
        }
        super().__init__(custom_patterns=medical_patterns)
```

### Integration with External Services

Send PII detection alerts to external systems:

```python
def pii_guardrail_check(state: SolutionState):
    # ... existing code ...

    if pii_result.pii_found:
        # Send alert to monitoring system
        send_alert_to_splunk(guardrail_error)
        send_notification_to_slack(session_id, pii_result.pii_types)

        # ... continue with error creation ...
```

### NLP-Based Enhancement (Future)

For detecting names, addresses, and contextual PII:

```python
# Future enhancement using spaCy or transformers
from transformers import pipeline

class NLPPIIDetector(PIIDetector):
    def __init__(self):
        super().__init__()
        self.ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")

    def detect(self, text: str, session_id: str):
        # First run regex detection
        regex_result = super().detect(text, session_id)

        # Then enhance with NER for names/locations
        ner_entities = self.ner_pipeline(text)

        # Combine results...
        return combined_result
```

### Guardrail Bypass (Development Only)

For testing purposes, add a bypass flag:

```python
# config/settings.py
GUARDRAIL_BYPASS_ENABLED = os.getenv("GUARDRAIL_BYPASS", "false").lower() == "true"

# graph/nodes.py
def pii_guardrail_check(state: SolutionState):
    if GUARDRAIL_BYPASS_ENABLED:
        print("⚠️  GUARDRAIL BYPASS ENABLED - PII check skipped")
        return {"messages": state["messages"]}

    # ... normal PII check logic ...
```

**WARNING**: Never enable bypass in production!

## Design Philosophy

### Why Regex-Based?

The implementation uses regex patterns instead of heavy ML/NLP frameworks because:

1. **Simplicity**: No external dependencies, easy to understand and maintain
2. **Performance**: Regex is fast and deterministic
3. **Transparency**: Patterns are visible and auditable
4. **Reliability**: No model training, versioning, or drift issues
5. **Sufficiency**: Regex handles structured PII (email, SSN, phone, credit cards) effectively

### Why Not NeMo Guardrails?

While NeMo Guardrails is powerful, it was not used because:

1. **Complexity**: Adds significant architectural overhead
2. **Dependencies**: Requires additional packages and LLM calls
3. **Overkill**: Full framework not needed for simple PII detection
4. **Latency**: Regex is faster than LLM-based checks
5. **Cost**: No API calls needed for pattern matching

### Extensibility

The architecture supports future enhancements:

- Add ML-based name/address detection
- Integrate with external PII services (AWS Macie, Google DLP)
- Implement confidence scoring
- Add context-aware detection
- Support multiple languages

All while maintaining the simple core regex-based foundation.

## Summary

The PII Detection Guardrails system provides:

- ✅ **Early Detection**: First step in workflow prevents PII propagation
- ✅ **Simple Implementation**: Regex-based, no external dependencies
- ✅ **Configurable**: Easy to add/remove PII patterns
- ✅ **Transparent**: Clear error reporting with session tracking
- ✅ **Performant**: Fast pattern matching with compiled regex
- ✅ **Secure**: Configurable PII masking in error outputs
- ✅ **Extensible**: Architecture supports future ML enhancements

For questions or issues, refer to the code in:
- `guardrails/pii_detector.py` - Core detection logic
- `graph/nodes.py:65` - Guardrail node implementation
- `guardrails/config.py` - Pattern configuration
- `models/data_models.py:197` - Data models

## References

- [Microsoft Presidio](https://microsoft.github.io/presidio/) - PII detection and anonymization
- [DataFog Python](https://github.com/DataFog/datafog-python) - Lightweight PII detection
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) - LLM guardrails framework
- [Elastic PII Detection](https://www.elastic.co/observability-labs/blog/pii-ner-regex-assess-redact-part-1) - NLP and regex patterns
