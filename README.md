# Chunker API Service

## Overview
Chunker is a FastAPI service that processes educational lesson content by breaking it into optimized semantic chunks for more effective processing and retrieval. The service employs a recursive chunking strategy to intelligently split text while preserving semantic meaning and contextual relationships.

## Installation

### Prerequisites
- Python 3.10+
- pip package manager

### Setup
1. Clone the repository
```bash
git clone https://github.com/abdushakurob/edtry-chunker chunker
cd chunker
```

2. Install required dependencies
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following variables:
```
EDTRY_INTERNAL_API_KEY=your_api_key_here
LARAVEL_API_URL=your_laravel_endpoint_here
```

## Usage

### Starting the Service
Run the FastAPI server using uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Authentication
This service requires API key authentication for all requests. The API key must be included in the `X-Internal-API-Key` header.

**Important:** The API key value must match the `EDTRY_INTERNAL_API_KEY` value set in your `.env` file. All requests without a valid API key will be rejected with a 401 Unauthorized response.

```python
# API key verification in the application
async def verify_api_key(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
```

### API Endpoint
Send a POST request to the `/chunk` endpoint with your lesson content:

```bash
curl -X POST http://localhost:8000/chunk \
  -H "Content-Type: application/json" \
  -H "X-Internal-API-Key: your_api_key_here" \
  -d '{
    "course_id": 123,
    "lesson_id": 456,
    "lesson_title": "Introduction to Machine Learning",
    "lesson_content": "Machine learning is a branch of artificial intelligence...",
    "type": "created"
  }'
```

### Request Format

**Headers**:
```
Content-Type: application/json
X-Internal-API-Key: your_api_key_here  # Must match EDTRY_INTERNAL_API_KEY in .env
```

**Body**:
```json
{
  "course_id": 123,
  "lesson_id": 456,
  "lesson_title": "Example Lesson Title",
  "lesson_content": "Your lesson content to be chunked...",
  "type": "created"  // Options: "created", "updated", "deleted"
}
```

### Response
```json
{
  "message": "Chunking request accepted and processing in background."
}
```

## How Chunking Works

### Recursive Chunking Strategy
The service utilizes the `RecursiveChunker` from the chonkie library to implement a sophisticated chunking algorithm:

1. **Tokenization**: Text is first tokenized using the "BAAI/bge-base-en-v1.5" tokenizer, a state-of-the-art embedding model that understands semantic relationships
2. **Size-based Splitting**: Content is split into chunks with approximately 400 tokens each
3. **Semantic Preservation**: The algorithm maintains semantic coherence by avoiding splits in the middle of sentences or logical units
4. **Minimum Character Threshold**: Each chunk must contain at least 100 characters to ensure meaningful content blocks

### Chunking Parameters
- **Chunk Size**: 400 tokens per chunk (optimized for embedding models)
- **Minimum Characters**: 100 characters per chunk
- **Tokenizer**: BAAI/bge-base-en-v1.5 for accurate token counting

## Chunking Workflow

1. **Content Reception**: The service receives lesson content via API endpoint
2. **Preprocessing**: Content is cleaned and normalized before chunking
3. **Recursive Chunking**: The `RecursiveChunker` algorithm splits the content while preserving semantic meaning
4. **Metadata Enrichment**: Each chunk is indexed and enriched with metadata (position, lesson reference)
5. **Downstream Processing**: Chunked content is sent to the Laravel backend for storage and further processing

## Benefits of the Chunking Approach

- **Improved Semantic Search**: Smaller, coherent chunks enable more precise search and retrieval
- **Enhanced Context Preservation**: The recursive algorithm maintains relationships between text segments
- **Optimized for Embedding Models**: 400-token chunks are ideal for most embedding and vector search systems
- **Processing Efficiency**: Background processing with automatic retries ensures reliable chunk handling

## Technical Implementation

### Chunking Algorithm Details

```python
chunker = RecursiveChunker(
    chunk_size=400,
    tokenizer_or_token_counter=lambda text: len(tokenizer.encode(text).ids),
    min_characters_per_chunk=100
)
```

The chunking process follows these technical steps:

1. **Tokenization**: The lesson content is analyzed using the BAAI/bge-base-en-v1.5 tokenizer
2. **Recursive Analysis**: The algorithm recursively identifies natural break points in the text
3. **Token Counting**: Each potential chunk's token count is evaluated against the target size
4. **Optimal Split Determination**: The algorithm determines the most semantically appropriate split points
5. **Chunk Generation**: Final chunks are created with proper indexing and relationship tracking

### Chunk Processing Pipeline

```
Input Text → Tokenization → Recursive Splitting → Chunk Indexing → Metadata Attachment → Laravel Backend
```

## Chunk Output Format

The chunking process produces an array of structured chunks with metadata:

```json
{
  "chunks": [
    {
      "text": "This is the first semantic chunk of the lesson content...",
      "chunk_index": 0
    },
    {
      "text": "This is the second chunk with related content...",
      "chunk_index": 1
    }
  ]
}
```

Each chunk includes:
- **Text Content**: The actual text segment
- **Chunk Index**: Sequential identifier for ordering and relationships
- **Implicit Relationships**: Chunks maintain their sequential relationship to preserve context

## Advanced Chunking Considerations

### Handling Edge Cases
The chunking algorithm includes special handling for:
- **Very Short Content**: Content below minimum thresholds is preserved as a single chunk
- **Code Blocks**: Special handling to avoid breaking code segments
- **Lists and Tables**: Preservation of structural elements when possible
- **Headers and Section Breaks**: Natural break points are preferred for chunking

### Performance Optimization
- **Asynchronous Processing**: Chunking occurs in background tasks to maintain API responsiveness
- **Memory Efficiency**: Streaming approach for handling large lesson content
- **Exponential Backoff**: Automatic retries ensure reliable delivery of chunks

## Maintenance and Monitoring

### Logs
Monitor application logs for chunking performance and errors:
```bash
tail -f chunker.log
```

### Common Issues
- **Tokenization Errors**: Ensure the BAAI tokenizer is properly installed
- **Connection Failures**: Check Laravel API endpoint availability and network connectivity
- **Authentication Errors**: Verify that the API keys match between services

### Security Considerations
- **API Key Management**: Rotate the API key periodically for enhanced security
- **Environment Variables**: Never hardcode the API key in the application code
- **Key Transmission**: Always use HTTPS in production to protect API key transmission
- **Access Logs**: Monitor access logs for unauthorized access attempts
- **Firewall Rules**: Consider restricting access to the API endpoint by IP address

### Performance Tuning
For larger lessons, you can adjust the chunking parameters in `app.py`:
```python
chunker = RecursiveChunker(
    chunk_size=400,  # Adjust based on your embedding model requirements
    tokenizer_or_token_counter=lambda text: len(tokenizer.encode(text).ids),
    min_characters_per_chunk=100  # Adjust for minimum chunk size
)
```
