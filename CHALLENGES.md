# 🔧 Challenges Faced & Solutions

## 1. ChromaDB Installation Failed on Windows
**Problem:** ChromaDB required Microsoft C++ Build Tools to compile `chroma-hnswlib`. Installation failed with:
```
error: Microsoft Visual C++ 14.0 or greater is required
```
**Solution:** Replaced ChromaDB with a pure numpy-based vector similarity search. Used cosine similarity with normalized embeddings stored as pickle files. This actually reduced dependencies and made the codebase more portable. No C++ compiler needed.

**Learning:** Always check platform compatibility of libraries before choosing them. Pure numpy cosine similarity performs comparably to ChromaDB for small-to-medium datasets.

---

## 2. Supabase PostgreSQL Blocked in India
**Problem:** Supabase free tier PostgreSQL was completely inaccessible from India due to network restrictions. Connection timed out consistently.

**Solution:** Switched to Railway.app MySQL which worked perfectly from India. Updated all database code from psycopg2 to mysql-connector-python.

**Learning:** Always have a backup database provider. Cloud service availability varies by region.

---

## 3. Gemini API Quota Exhausted
**Problem:** Gemini 1.5 Flash free tier has daily request limits. During development and testing, quota was exhausted frequently causing 429 errors.

**Solution:** Built a 3-tier LLM fallback system:
1. Gemini 2.0 Flash (primary)
2. Ollama + local model (secondary)
3. Rule-based keyword matching (emergency)

This turned a problem into a production feature — the system never goes completely dark.

**Learning:** Never rely on a single API in production. Fallback architecture is essential for reliability.

---

## 4. Local LLM (Ollama) Response Verbosity
**Problem:** Qwen3:4b and Mistral 7b models gave extremely verbose responses with markdown headers, bullet points, and disclaimers — unsuitable for a chat interface.

**Solution:** 
- Added `/no_think` flag to disable Qwen3 thinking mode
- Tuned temperature to 0.2 for focused responses
- Added post-processing to extract first sentence only
- Reduced num_predict to limit response length
- Switched to phi3:mini which follows instructions better on CPU

**Learning:** Smaller instruction-tuned models often outperform larger general models for specific constrained tasks like RAG chatbots.

---

## 5. Python Version and SSL Issues
**Problem:** Microsoft Store Python 3.9 had broken SSL certificates, preventing pip from connecting to PyPI. Virtual environment creation also failed.

**Solution:** Installed official Python 3.14 from python.org. Discovered multiple Python versions (3.7, 3.9, 3.14, Anaconda 3.8) were installed. Used `py -3.14 -m venv venv` to create environment with correct version.

**Learning:** Always install Python from python.org, not Microsoft Store. Use `py -0` to list all installed versions.

---

## 6. Ollama Not in System PATH
**Problem:** Ollama was installed but terminal couldn't find the `ollama` command. Models were stored at `C:\Users\Username\.ollama\models` but executable wasn't in PATH.

**Solution:** The code doesn't actually need the `ollama` command — it communicates directly with the Ollama HTTP API at `http://localhost:11434`. As long as the Ollama app is running, the fallback works perfectly without PATH configuration.

**Learning:** Understanding how tools communicate (HTTP API vs CLI) helps work around environment issues.

---

## 7. PDF Content Not Loading Correctly
**Problem:** PDFs converted from TXT using online converters created image-based PDFs. PyPDF2 couldn't extract text from image PDFs, resulting in empty content.

**Solution:** Converted TXT files to PDF via Microsoft Word → Save As PDF, which creates proper text-based PDFs that PyPDF2 can extract from.

**Learning:** Not all PDFs are equal — text-based vs image-based PDFs require different processing approaches.

---

## 8. RAG Retrieving Wrong Context
**Problem:** Rule-based fallback was triggered when LLM timed out, returning incorrect answers. For example "Where is gynecology OPD?" returned OPD timings because rule-based matched "OPD" keyword.

**Solution:** 
- Increased LLM timeout to 180 seconds
- Switched from Mistral 7b to phi3:mini for faster CPU inference
- Improved rule-based keyword matching with more specific conditions

**Learning:** RAG quality depends on both retrieval accuracy AND LLM response quality. A slow LLM that times out is worse than a fast rule-based system.

---

## 9. Frontend Chatbot Showing Empty Green Boxes
**Problem:** Bot responses appeared as empty green boxes in the chat interface. Text was being returned from API but not displaying.

**Solution:** The issue was markdown formatting in LLM responses conflicting with innerHTML rendering. Fixed by adding markdown stripping in the JavaScript appendMessage function:
```javascript
div.innerHTML = text
  .replace(/\*\*(.*?)\*\*/g, '$1')
  .replace(/#{1,3} /g, '')
  .replace(/\n/g, ' ');
```

**Learning:** Always sanitize LLM output before rendering in HTML — models may return unexpected formatting.

---

## 10. Database Connection Issues
**Problem:** Initial DATABASE_URL was incorrectly formatted, mixing HTTPS URL format with PostgreSQL connection string format.

**Solution:** Correct PostgreSQL URI format:
```
postgresql://user:password@host:5432/database
```
Not:
```
postgresql://user:password@https://host/database
```

**Learning:** Connection string formats are strict — always copy from official documentation rather than constructing manually.

---

## Summary

| Challenge | Root Cause | Solution |
|---|---|---|
| ChromaDB failed | C++ dependency | Pure numpy vectors |
| Supabase blocked | India network restriction | Railway MySQL |
| Gemini quota | Free tier limits | 3-tier LLM fallback |
| Verbose LLM | Model behavior | Prompt tuning + phi3:mini |
| Python SSL | Microsoft Store Python | Official python.org install |
| Ollama PATH | Environment config | Direct HTTP API usage |
| PDF unreadable | Image-based PDF | Word → Save as PDF |
| Wrong RAG answers | LLM timeout → rule-based | Faster model + longer timeout |
| Empty chat boxes | Markdown in HTML | JavaScript markdown stripping |
| DB connection | Wrong URL format | Correct URI format |
