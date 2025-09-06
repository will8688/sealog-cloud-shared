# Yacht Data Enhancement Engine - Integration Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install aiohttp requests streamlit
```

### 2. Drop the File
Simply save `yacht_data_enhancer.py` in your project directory alongside your existing Streamlit app.

### 3. Import and Use
```python
from yacht_data_enhancer import enhance_yacht_data, enhance_yacht_data_batch

# Single yacht enhancement
enhanced_data = enhance_yacht_data("Eclipse")
st.write(f"Length: {enhanced_data['length']}m")

# Batch enhancement with progress
def update_progress(current, total, yacht_name):
    progress_bar.progress(current / total)
    status_text.text(f"Processing {yacht_name} ({current}/{total})")

progress_bar = st.progress(0)
status_text = st.empty()

enhanced_yachts = enhance_yacht_data_batch(
    yacht_list, 
    progress_callback=update_progress
)
```

## Integration Examples

### Basic Enhancement
```python
import streamlit as st
from yacht_data_enhancer import enhance_yacht_data

# In your existing app
yacht_name = st.selectbox("Select Yacht", your_yacht_list)

if st.button("Enhance Data"):
    enhanced = enhance_yacht_data(yacht_name)
    
    # Merge with your existing data
    your_yacht_data.update({
        'length': enhanced.get('length'),
        'year_built': enhanced.get('year_built'),
        'builder': enhanced.get('builder'),
        # ... other fields
    })
```

### Bulk Enhancement for Existing Data
```python
import pandas as pd
from yacht_data_enhancer import enhance_yacht_data_batch

# Enhance your entire yacht database
df = pd.read_csv('your_yacht_data.csv')

# Create progress tracking
progress_bar = st.progress(0)
status_text = st.empty()

def progress_callback(current, total, yacht_name):
    progress_bar.progress(current / total)
    status_text.text(f"Enhancing {yacht_name} ({current}/{total})")

# Enhance all yachts
enhanced_data = enhance_yacht_data_batch(
    df['yacht_name'].tolist(),
    progress_callback=progress_callback
)

# Convert to DataFrame and merge
enhanced_df = pd.DataFrame(enhanced_data)
merged_df = df.merge(enhanced_df, left_on='yacht_name', right_on='name', how='left')
```

### Smart Data Merging
```python
def merge_with_existing_data(existing_data, enhanced_data):
    """Merge enhanced data with existing, keeping best values"""
    
    for key, new_value in enhanced_data.items():
        if new_value and new_value != 'N/A':
            # Only update if we don't have the data or confidence is high
            if (key not in existing_data or 
                not existing_data[key] or 
                enhanced_data.get('confidence_score', 0) > 0.7):
                existing_data[key] = new_value
    
    return existing_data

# Usage
for yacht in your_yacht_database:
    enhanced = enhance_yacht_data(yacht['name'])
    yacht = merge_with_existing_data(yacht, enhanced)
```

## Return Data Structure

```python
{
    'name': 'Eclipse',
    'imo': '1234567',
    'mmsi': '123456789',
    'length': 162.5,
    'beam': 22.0,
    'year_built': 2010,
    'builder': 'Blohm+Voss',
    'designer': 'Terence Disdale',
    'owner': 'Roman Abramovich',
    'flag': 'Bermuda',
    'gross_tonnage': 13564.0,
    'max_speed': 25.0,
    'cruise_speed': 22.0,
    'guests': 36,
    'crew': 70,
    'price': '$1.5B',
    'location': 'Mediterranean',
    'yacht_type': 'Motor Yacht',
    'sources': ['SuperYacht Times', 'MarineTraffic'],
    'confidence_score': 0.85,
    'last_updated': '2025-01-15 14:30:22'
}
```

## Configuration Options

### Custom Rate Limiting
```python
from yacht_data_enhancer import YachtDataEnhancer, MarineTrafficAdapter

# Create custom enhancer with slower rate limits
enhancer = YachtDataEnhancer()
enhancer.adapters[0].rate_limit = 3.0  # 3 seconds between requests
```

### Adding Custom Sources
```python
from yacht_data_enhancer import DataSourceAdapter, YachtData

class YourCustomAdapter(DataSourceAdapter):
    def __init__(self):
        super().__init__("YourSource", "https://yoursource.com", 1.0)
    
    async def search(self, yacht_name):
        # Your custom search logic
        return YachtData(name=yacht_name, sources=[self.name])

# Add to enhancer
enhancer = get_enhancer()
enhancer.adapters.append(YourCustomAdapter())
```

## Error Handling

The system is designed to be robust:
- Failed sources don't break the entire search
- Cached results prevent repeated API calls
- Rate limiting respects server resources
- Confidence scores help you evaluate data quality

## Performance Tips

1. **Use batch processing** for multiple yachts
2. **Cache results** are automatic but consider persistent storage
3. **Rate limiting** prevents getting blocked by sources
4. **Run during off-peak hours** for large datasets

## Legal Considerations

- Always check `robots.txt` and terms of service
- Respect rate limits (built into the system)
- Consider reaching out to data providers for API access
- For commercial use, consider data licensing agreements

## Troubleshooting

### Common Issues:
1. **Slow responses**: Increase rate limits or reduce concurrent requests
2. **No data found**: Check yacht name spelling, try variations
3. **Blocked requests**: Implement longer delays, check robots.txt
4. **Memory issues**: Process in smaller batches

### Debug Mode:
```python
import logging
logging.getLogger('yacht_data_enhancer').setLevel(logging.DEBUG)
```

## Next Steps

1. Test with a few yacht names first
2. Gradually increase batch sizes
3. Monitor success rates and adjust rate limits
4. Consider adding more data sources
5. Implement persistent caching for large datasets

The system is designed to be "drop-in" ready - just import and start using the `enhance_yacht_data()` function in your existing Streamlit app!