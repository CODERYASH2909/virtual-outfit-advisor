# 👔 Virtual Outfit Advisor (VOA)

A **production-ready AI-powered web application** that helps users build a **Digital Wardrobe**, receive **personalized outfit recommendations**, and generate **smart travel packing suggestions** based on wardrobe contents, weather conditions, body attributes, and personal preferences.

The application combines **Computer Vision**, **Machine Learning**, **Recommendation Algorithms**, and **Weather Intelligence** to provide an intelligent fashion assistant.

---

# 🚀 Tech Stack

| Layer | Technology |
|--------|------------|
| **Frontend** | HTML5, CSS3, TypeScript, Tailwind CSS |
| **Backend** | Python, Django, Django REST Framework |
| **Database** | PostgreSQL |
| **Computer Vision** | YOLOv8, OpenCV, MediaPipe |
| **Machine Learning** | Scikit-learn |
| **Recommendation Algorithms** | Content-Based Filtering, Cosine Similarity, Random Forest |
| **Weather API** | OpenWeatherMap |
| **Deployment** | Docker, Docker Compose, Gunicorn, WhiteNoise, Nginx |

---

# 📁 Project Structure

```text
voa/
│
├── backend/
│   ├── voa_backend/
│   ├── accounts/
│   ├── wardrobe/
│   ├── recommendations/
│   ├── travel/
│   ├── ai_engine/
│   │   ├── clothing_detection/
│   │   ├── body_detection/
│   │   ├── color_detection/
│   │   ├── recommendation_engine/
│   │   └── utils/
│   ├── favorites/
│   ├── core/
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── pages/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
│
├── docker-compose.yml
└── README.md
```

---

# ✨ Features

## 🔐 Authentication

- User Registration
- Secure Login (JWT Authentication)
- Forgot Password
- Reset Password
- User Profile Management

---

## 👕 Digital Wardrobe

- Upload Clothing Images
- Organize Wardrobe
- Edit & Delete Clothing
- Search & Filter
- Clothing Categories
- Favorites
- Wardrobe Statistics

---

## 🤖 AI Clothing Detection

Automatically detects clothing items from uploaded images.

### Algorithms

- YOLOv8

### Capabilities

- Clothing Detection
- Clothing Classification
- Multiple Item Detection
- Background Separation

---

## 🎨 Color Detection

Automatically identifies dominant clothing colors.

### Algorithm

- OpenCV

### Capabilities

- Dominant Color Detection
- Multiple Color Detection
- Color Classification
- Color Palette Generation

---

## 🧍 Body Detection

Detects body landmarks and proportions.

### Algorithm

- MediaPipe

### Capabilities

- Body Landmark Detection
- Body Alignment
- Clothing Position Analysis

---

## 👗 Intelligent Outfit Recommendation

Generates personalized outfit recommendations based on:

- Wardrobe Items
- Occasion
- Weather
- Season
- Favorite Colors
- Clothing Compatibility
- User Preferences
- Recommendation History

### Algorithms

- Content-Based Filtering
- Cosine Similarity
- Random Forest

---

## 🌦 Weather Intelligence

Provides live weather information.

### Weather Data

- Temperature
- Humidity
- Wind Speed
- Rain Forecast
- UV Index

### API

- OpenWeatherMap

---

## ✈️ Travel Planner

Generates intelligent packing recommendations.

### Features

- Destination Weather
- Smart Packing Checklist
- Outfit Suggestions
- Missing Clothing Detection
- Packing Summary

---

## ❤️ Favorites

- Save Outfits
- Save Recommendations
- Favorite Clothing

---

## 📜 Recommendation History

- Previous Recommendations
- Weather History
- Outfit Analytics

---

## 📊 Dashboard

- Wardrobe Statistics
- Recommendation Summary
- Recent Activity
- Favorite Outfits

---

# 🧠 Algorithms Used

| Module | Algorithm / Technology |
|----------|------------------------|
| Clothing Detection | YOLOv8 |
| Color Detection | OpenCV |
| Body Detection | MediaPipe |
| Feature Extraction | Computer Vision |
| Outfit Recommendation | Content-Based Filtering |
| Similarity Matching | Cosine Similarity |
| Outfit Ranking | Random Forest |
| Weather Forecast | OpenWeatherMap API |

---

# 🔌 API Overview

| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/auth/register/` | POST | Register User |
| `/auth/login/` | POST | User Login |
| `/auth/profile/` | GET / PATCH | User Profile |
| `/wardrobe/items/` | GET / POST | Manage Wardrobe |
| `/recommendations/generate/` | POST | Generate Recommendation |
| `/recommendations/history/` | GET | Recommendation History |
| `/travel/plans/` | GET / POST | Travel Planner |
| `/favorites/` | GET / POST | Favorite Outfits |

---

# 🔒 Security

- JWT Authentication
- Password Encryption
- Secure File Upload
- Role-Based Authorization
- User Data Isolation
- Input Validation
- CORS Protection

---

# 🏗 System Architecture

```text
                  User
                    │
                    ▼
          Frontend (TypeScript)
                    │
                    ▼
        Django REST Framework API
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
 AI Engine      PostgreSQL    Weather API
     │                              │
     └──────────────┬───────────────┘
                    ▼
        Outfit Recommendation Engine
                    │
                    ▼
        Personalized Outfit Suggestions
```

---

# 🎯 Design Principles

- Modular Architecture
- Clean Code
- RESTful APIs
- Scalable Project Structure
- AI-Powered Recommendation Engine
- Weather-Aware Decision Making
- Secure Authentication
- Responsive User Interface
- High Maintainability

---

# 🚀 Future Enhancements

- Virtual Try-On
- Fashion Trend Prediction
- Mobile Application
- Smart Notifications


---

# 📄 License

This project is developed for educational, research, and commercial purposes.

---

## ⭐ If you like this project, don't forget to star the repository!