# 🎓 Enhanced Study Plan Mode - Feature Guide

## Overview

Your StudyPlan AI now has **two powerful modes** for generating study plans:

### 📚 **Basic Mode**
- Generates structured study plans from your course documents
- Includes weekly topics, activities, and time estimates
- Perfect for quick study plan generation

### ⭐ **Enhanced Mode** (NEW!)
- Everything in Basic Mode PLUS:
- **YouTube video recommendations** for each topic
- **Curated learning resources** matched to your content
- **Optional syllabus integration** for timeline alignment
- **Richer, more detailed study plans**

---

## 🚀 How to Use Enhanced Mode

### Step 1: Upload Your Documents
1. Go to the **Upload** page
2. Select **"Enhanced Mode"** (the card with the YouTube icon)
3. Upload your **course handout/notes** (required)
4. Optionally upload your **course syllabus** for better timeline alignment

### Step 2: Generate Study Plan
1. Click **"Analyze Document"**
2. The AI will:
   - Analyze your documents
   - Extract key concepts and topics
   - Search for relevant YouTube videos
   - Create a comprehensive study plan with resources

### Step 3: Study with Resources
1. View your study plan
2. Each week now includes:
   - **Study activities** (reading, practice, projects)
   - **YouTube video tutorials** with thumbnails and durations
   - **Direct links** to educational content
   - **Channel names** and video descriptions

---

## 🎯 Key Features

### YouTube Integration
- **Automatic video search** based on topics
- **High-quality educational content** prioritized
- **Video thumbnails** for quick preview
- **Duration display** to plan your time
- **Channel information** to find trusted creators

### Syllabus Integration
- Upload your course syllabus alongside handouts
- AI aligns study plan with official course timeline
- Highlights important deadlines and milestones
- Ensures coverage of all syllabus topics

### Smart Resource Matching
- Videos matched to specific concepts
- Curated educational channels by subject:
  - **Math**: 3Blue1Brown, Khan Academy, PatrickJMT
  - **Programming**: freeCodeCamp, Traversy Media, Corey Schafer
  - **Physics**: Physics Girl, MinutePhysics
  - **Chemistry**: NileRed, Organic Chemistry Tutor
  - And many more!

---

## 🔧 Technical Details

### New Database Models
- **LearningResource**: Stores YouTube videos and other resources
- **Enhanced StudyPlan**: Includes mode selection and syllabus reference
- **Document Types**: Handout, Syllabus, Textbook, Other

### API Integration
- YouTube Data API v3 for video search
- Fallback to direct YouTube search if API key not configured
- Smart caching to avoid redundant API calls

### Files Modified
1. **pdf/models.py** - New models for resources and enhanced plans
2. **pdf/views.py** - Updated upload and analyze views
3. **youtube_helper.py** - YouTube API integration
4. **study_plan_prompts.py** - Enhanced AI prompts
5. **templates/upload_simple.html** - Mode selection UI
6. **templates/study_plan_detail.html** - Resource display

---

## 📝 Configuration (Optional)

### YouTube API Key
To enable full YouTube integration with video details:

1. Get a YouTube Data API v3 key from [Google Cloud Console](https://console.cloud.google.com/)
2. Add to your `.env` file:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```
3. Without API key, the app will generate YouTube search links instead

---

## 💡 Tips for Best Results

### For Enhanced Mode:
1. **Upload clear, well-structured documents** - Better content = Better recommendations
2. **Include syllabus when available** - Helps AI understand course structure
3. **Use descriptive file names** - Helps with organization
4. **Review video recommendations** - Click through to find your favorites

### For Video Learning:
1. **Watch videos before reading** - Visual explanations help comprehension
2. **Take notes while watching** - Use the notes field in activities
3. **Explore recommended channels** - Subscribe to your favorites
4. **Adjust playback speed** - 1.25x or 1.5x for efficiency

---

## 🎨 UI Improvements

### Mode Selection
- **Visual cards** for easy mode selection
- **Clear descriptions** of each mode
- **Responsive design** for mobile and desktop

### Resource Display
- **Video thumbnails** with hover effects
- **Duration badges** on thumbnails
- **Channel names** and descriptions
- **External link indicators**
- **Grid layout** for easy browsing

---

## 🐛 Troubleshooting

### Videos Not Showing?
- Check if you selected "Enhanced Mode" before uploading
- Ensure your document has clear topic names
- Try regenerating the study plan

### Upload Issues?
- Ensure PDFs are under 50MB
- Check file format (PDF only)
- Try refreshing the page

### API Errors?
- YouTube API key may be invalid or expired
- App will fall back to search links automatically
- No functionality is lost without API key

---

## 🔮 Future Enhancements

Potential additions:
- Article and documentation links
- Interactive quizzes from video content
- Progress tracking per resource
- Bookmark favorite videos
- Community-shared resource lists
- AI-generated practice problems

---

## 📞 Support

If you encounter any issues or have suggestions:
1. Check the console for error messages
2. Verify your documents are properly formatted
3. Try Basic Mode if Enhanced Mode has issues
4. Review this guide for configuration tips

---

**Enjoy your enhanced learning experience! 🚀📚**

