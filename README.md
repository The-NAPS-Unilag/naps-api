# Complete API Documentation

For full route reference, see `docs/API_ROUTES.md`

## Important Notes for Frontend Developers

### Field Naming Conventions
- **User profile**: Use `current_level` (not `level`) when referencing the user's academic level
- **Login response**: Returns `is_super_admin` and `is_active` fields in addition to other user fields

### Known Quirks
- **Forum send message**: The response returns the message object under the key `message_data` (not `message`)
- **Admin login**: Requires both `X-API-Key` header AND valid admin credentials

### Recent Updates (March 2026)
- Login response now includes `is_super_admin` and `is_active` fields
- Forum message response uses `message_data` key for the message object

## Getting Started

### Base URL
All API endpoints start with: `https://your-domain.com/api`

### Authentication Requirements
Some endpoints require two things:

1. **API Key** - Include in request headers as `X-API-Key` (just admin , dont think)


2. **JWT Token** - Include in request headers as `Authorization: Bearer <token>`

### Common Response Format
```json
{
  "message": "Success message or error description",
  "data": {...}, // Response data (varies by endpoint)
  "error": "Error details" // Only present on errors
}
```

---

## 🏠 Hello Route

### Get Welcome Message
**GET** `/`

**Response (200):**
```html
<p>Hello, developers! All routes start with /api.</p>
```

---

## 🔐 Authentication & API Keys

### 1. Generate API Key (Test)
**POST** `/test_generate_api_key`

⚠️ **Note**: This is a test endpoint without authentication (marked as TODO FIX UP)

**Response (201):**
```json
{
  "message": "Test API key generated successfully",
  "api_key": "generated-api-key-string"
}
```

### 2. Generate API Key (Admin)
**POST** `/generate_api_key`

**Headers:**
```
Authorization: Bearer admin-jwt-token
```

**Response (201):**
```json
{
  "message": "API key generated successfully",
  "api_key": "generated-api-key-string"
}
```

### 3. List All API Keys (Admin)
**GET** `/api_keys`

**Headers:**
```
Authorization: Bearer admin-jwt-token
```

**Response (200):**
```json
[
  {
    "id": 1,
    "key": "api-key-string",
    "created_at": "2024-01-15T10:30:00",
    "is_active": true
  }
]
```

### 4. Delete API Key (Admin)
**DELETE** `/api_keys/{api_key_id}`

**Headers:**
```
Authorization: Bearer admin-jwt-token
```

**Response (200):**
```json
{
  "message": "API key deleted successfully"
}
```

---

## 👤 User Management

### 1. Create User Account
**POST** `/users`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: multipart/form-data
```

**Form Data:**
```javascript
const formData = new FormData();
formData.append('firstname', 'John');
formData.append('lastname', 'Doe');
formData.append('email', 'john@example.com');
formData.append('current_level', '300');
formData.append('matric_no', 'CSC/2021/001');
formData.append('password', 'securepassword');
// Optional files
formData.append('profile_picture', fileObject);
formData.append('departmental_fees', fileObject);
```

**Success Response (201):**
```json
{
  "message": "User created successfully. Please check your email for verification.",
  "user": {
    "id": 123,
    "email": "john@example.com",
    "firstname": "John",
    "lastname": "Doe"
  }
}
```

### 2. Verify Email
**POST** `/users/confirm`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "email": "john@example.com",
  "otp": "123456"
}
```

### 3. Resend OTP
**POST** `/users/resend-otp`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "email": "john@example.com"
}
```

### 4. Login with Email
**POST** `/users/login`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Success Response (200):**
```json
{
  "access_token": "jwt-token-here",
  "user": {
    "id": 123,
    "email": "john@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "department": "Computer Science",
    "current_level": "300",
    "matric_no": "CSC/2021/001",
    "profile_picture": "https://s3-url.com/image.jpg",
    "departmental_fees": "https://s3-url.com/receipt.jpg",
    "bio": "Student bio",
    "is_admin": false,
    "is_super_admin": false,
    "is_verified": true,
    "is_mentor": false,
    "is_active": true,
    "is_confirmed": true,
    "mentor": {
      "id": 456,
      "firstname": "Jane",
      "lastname": "Smith",
      "email": "jane@example.com",
      "profile_picture": "https://s3-url.com/mentor.jpg"
    }
  }
}
```

### 5. Login with Matric Number
**POST** `/users/login/matric`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "matric_no": "CSC/2021/001",
  "password": "securepassword"
}
```

**Success Response (200):** Same as email login

### 6. Get Current User
**GET** `/users/me`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "id": 123,
  "email": "john@example.com",
  "firstname": "John",
  "lastname": "Doe",
  "current_level": "300"
  // ... other user fields
}
```

**Note:** This endpoint returns the profile of the currently authenticated user based on their JWT token.

### 7. List All Users (with Pagination)
**GET** `/users`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 10): Items per page

**Success Response (200):**
```json
{
  "users": [
    {
      "id": 123,
      "firstname": "John",
      "lastname": "Doe",
      "email": "john@example.com"
    }
  ],
  "total": 50,
  "pages": 5,
  "current_page": 1
}
```

### 8. Update User Profile
**PUT** `/users/update/{user_id}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: multipart/form-data
```

**Form Data:**
```javascript
const formData = new FormData();
formData.append('current_level', '400');
formData.append('bio', 'Updated bio text');
formData.append('profile_picture', newImageFile); // optional
```

### 9. Forgot Password
**POST** `/users/forgot-password`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "email": "john@example.com"
}
```

### 10. Reset Password
**POST** `/users/reset-password`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "email": "john@example.com",
  "otp": "123456",
  "new_password": "newpassword123"
}
```

### 11. Delete User Account
**DELETE** `/users/delete/{user_id}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "message": "Delete Successful"
}
```

---

## 📚 Resources Management

### 1. Upload Resource
**POST** `/api/resources/`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: multipart/form-data
```

**Form Data:**
```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('title', 'Data Structures Notes');
formData.append('author', 'Prof. Smith');
formData.append('course_title', 'CSC301');
formData.append('level', '300');
formData.append('contributors', 'John Doe'); // can add multiple
```

**Success Response (201):**
```json
{
  "message": "Resource uploaded successfully",
  "resource": {
    "id": 456,
    "title": "Data Structures Notes",
    "author": "Prof. Smith",
    "course_title": "CSC301",
    "level": "300",
    "file_url": "https://s3-url.com/file.pdf",
    "contributors": ["John Doe"],
    "uploaded_by": 123,
    "is_approved": false,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

### 2. Get Resources by Level
**GET** `/api/resources/level/{level}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Example:** `GET /api/resources/level/300`

**Success Response (200):**
```json
[
  {
    "id": 456,
    "title": "Data Structures Notes",
    "author": "Prof. Smith",
    "course_title": "CSC301",
    "level": "300",
    "file_url": "https://s3-url.com/file.pdf",
    "contributors": ["John Doe"],
    "uploaded_by": 123,
    "is_approved": true,
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### 3. Get Pending Resources (Admin)
**GET** `/api/resources/pending`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 4. Approve Resource (Admin)
**POST** `/api/resources/{resource_id}/approve`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Success Response (200):**
```json
{
  "message": "Resource approved successfully",
  "resource": {
    "id": 456,
    "title": "Data Structures Notes",
    "is_approved": true
    // ... other fields
  }
}
```

### 5. Delete Resource (Admin)
**DELETE** `/api/resources/{resource_id}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Success Response (200):**
```json
{
  "message": "Resource deleted successfully"
}
```

---

## 🎉 Events Management

### 1. Get All Events
**GET** `/api/events/`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
[
  {
    "id": 789,
    "name": "Tech Conference 2024",
    "description": "Annual technology conference",
    "date": "2024-03-15",
    "time": "09:00:00",
    "location": "Main Auditorium",
    "event_type": "conference",
    "capacity": 200,
    "rsvp_count": 45,
    "is_open_for_registration": true
  }
]
```

### 2. Get Event by ID
**GET** `/api/events/{event_id}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "id": 789,
  "name": "Tech Conference 2024",
  "description": "Annual technology conference",
  "date": "2024-03-15",
  "time": "09:00:00",
  "location": "Main Auditorium",
  "event_type": "conference",
  "capacity": 200,
  "rsvp_count": 45,
  "is_open_for_registration": true
}
```

### 3. Create Event
**POST** `/api/events/`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Study Group Session",
  "description": "Weekly study group for CSC301",
  "date": "2024-02-20",
  "time": "14:00",
  "location": "Library Room 203",
  "event_type": "study_group",
  "capacity": 20
}
```

**Success Response (201):**
```json
{
  "id": 790,
  "name": "Study Group Session",
  "message": "Event created successfully."
}
```

### 4. RSVP to Event
**POST** `/api/events/{event_id}/rsvp`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "event_id": 789,
  "message": "RSVP successful"
}
```

### 5. Cancel RSVP
**POST** `/api/events/{event_id}/cancel_rsvp`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "event_id": 789,
  "message": "RSVP cancelled successfully"
}
```

### 6. Get Events by Type
**GET** `/api/events/type/{event_type}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Example:** `GET /api/events/type/conference`

---

## 🤝 Mentorship System

### 1. Apply for Mentorship (as Student)
**POST** `/api/mentorship/apply`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: application/json
```

**Body:**
```json
{
  "matric_no": "CSC/2021/001",
  "level": "300",
  "areas_of_interest": "Web Development, Data Structures"
}
```

**Success Response (201):**
```json
{
  "message": "Mentorship application submitted successfully",
  "application": {
    "id": 101,
    "student_id": 123,
    "matric_no": "CSC/2021/001",
    "level": "300",
    "areas_of_interest": "Web Development, Data Structures",
    "status": "pending"
  }
}
```

### 2. Apply to be a Mentor
**POST** `/api/mentorship/apply-mentor`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: application/json
```

**Body:**
```json
{
  "phone_no": "+2348012345678",
  "academic_background": "Computer Science Graduate",
  "area_of_expertise": "Full Stack Development",
  "preferred_mode": "online"
}
```

**Success Response (201):**
```json
{
  "message": "Mentor application submitted successfully",
  "application": {
    "id": 201,
    "applicant_id": 123,
    "phone_no": "+2348012345678",
    "academic_background": "Computer Science Graduate",
    "area_of_expertise": "Full Stack Development",
    "preferred_mode": "online",
    "status": "pending"
  }
}
```

### 3. Get Pending Mentorship Applications (Admin)
**GET** `/api/mentorship/applications`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 4. Get Pending Mentor Applications (Admin)
**GET** `/api/mentorship/mentor-applications`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 5. Approve Mentor Application (Admin)
**POST** `/api/mentorship/mentor-applications/{application_id}/approve`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 6. Reject Mentor Application (Admin)
**POST** `/api/mentorship/mentor-applications/{application_id}/reject`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
Content-Type: application/json
```

**Body:**
```json
{
  "reason": "Insufficient experience"
}
```

### 7. Assign Mentor (Admin)
**POST** `/api/mentorship/assign-mentor`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
Content-Type: application/json
```

**Body:**
```json
{
  "mentorship_application_id": 101,
  "mentor_id": 456
}
```

### 8. Schedule Mentorship Session
**POST** `/api/mentorship/schedule-session`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: application/json
```

**Body:**
```json
{
  "mentorship_id": 102,
  "scheduled_time": "2024-02-15T14:00:00",
  "duration": 60,
  "notes": "Discuss web development career path"
}
```

### 9. Submit Session Feedback
**POST** `/api/mentorship/submit-feedback`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: application/json
```

**Body:**
```json
{
  "session_id": 301,
  "rating": 5,
  "comments": "Very helpful session"
}
```

### 10. Get My Mentorships
**GET** `/api/mentorship/my-mentorships`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "as_mentor": [
    {
      "id": 101,
      "mentee": {
        "id": 123,
        "firstname": "Jane",
        "lastname": "Doe"
      },
      "status": "active"
    }
  ],
  "as_mentee": [
    {
      "id": 102,
      "mentor": {
        "id": 456,
        "firstname": "John",
        "lastname": "Smith"
      },
      "status": "active"
    }
  ]
}
```

### 11. Get Mentorship Sessions
**GET** `/api/mentorship/mentorships/{mentorship_id}/sessions`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

### 12. Complete Mentorship
**POST** `/api/mentorship/mentorships/{mentorship_id}/complete`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

---

## 💬 Forums & Discussions

### 1. Get All Forums
**GET** `/api/forums/`

**Headers:**
```
X-API-Key: your-api-key
```

**Success Response (200):**
```json
[
  {
    "id": 1,
    "name": "General Discussion",
    "description": "General discussions for all students",
    "is_general": true,
    "member_count": 150,
    "created_at": "2024-01-01T00:00:00"
  }
]
```

### 2. Create Forum (Admin)
**POST** `/api/forums/`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Computer Science Discussion",
  "description": "Discussions related to CS courses",
  "is_general": false
}
```

**Success Response (201):**
```json
{
  "message": "Forum created successfully.",
  "forum": {
    "id": 2,
    "name": "Computer Science Discussion",
    "description": "Discussions related to CS courses",
    "is_general": false
  }
}
```

### 3. Join Forum
**POST** `/api/forums/{forum_id}/join`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "message": "Successfully joined forum"
}
```

### 4. Create Thread in Forum
**POST** `/api/forums/{forum_id}/threads`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: application/json
```

**Body:**
```json
{
  "title": "Help with Data Structures Assignment",
  "body": "I'm having trouble with implementing binary trees..."
}
```

**Success Response (201):**
```json
{
  "message": "Thread created successfully.",
  "thread": {
    "id": 501,
    "title": "Help with Data Structures Assignment",
    "body": "I'm having trouble with implementing binary trees...",
    "created_by": 123,
    "created_at": "2024-02-15T10:30:00"
  }
}
```

### 5. Get Thread Details
**GET** `/api/forums/threads/{thread_id}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "thread": {
    "id": 501,
    "title": "Help with Data Structures Assignment",
    "body": "I'm having trouble with implementing binary trees...",
    "created_by": 123,
    "created_at": "2024-02-15T10:30:00"
  },
  "messages": [
    {
      "id": 601,
      "content": "Have you tried using recursion?",
      "user": {
        "id": 456,
        "firstname": "Jane",
        "lastname": "Smith"
      },
      "created_at": "2024-02-15T11:00:00",
      "likes": 3,
      "attachment_url": null
    }
  ]
}
```

### 6. Send Message in Thread
**POST** `/api/forums/threads/{thread_id}/messages`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: multipart/form-data
```

**Form Data:**
```javascript
const formData = new FormData();
formData.append('content', 'Here is my response...');
formData.append('parent_message_id', '601'); // optional for replies
formData.append('attachment', fileObject); // optional
```

**Success Response (200):**
```json
{
  "message": "Message sent successfully.",
  "message_data": {
    "id": 602,
    "content": "Here is my response...",
    "thread_id": 501,
    "sent_by": 123,
    "created_at": "2024-02-15T11:30:00",
    "likes": 0,
    "attachment_url": "https://s3-url.com/file.pdf"
  }
}
```

### 7. Get Thread Messages
**GET** `/api/forums/threads/{thread_id}/messages`

**Headers:**
```
X-API-Key: your-api-key
```

### 8. Like Message
**POST** `/api/forums/messages/{message_id}/like`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
```

**Success Response (200):**
```json
{
  "message": "Message liked successfully.",
  "likes": 4
}
```

### 9. Explore Forums
**GET** `/api/forums/explore`

**Headers:**
```
X-API-Key: your-api-key
```

### 10. Get Recommended Forums
**GET** `/api/forums/recommended`

**Headers:**
```
X-API-Key: your-api-key
```

### 11. Get Top Contributors
**GET** `/api/forums/top-contributors`

**Headers:**
```
X-API-Key: your-api-key
```

**Success Response (200):**
```json
[
  {
    "id": 456,
    "firstname": "Jane",
    "lastname": "Smith",
    "profile_picture": "https://s3-url.com/jane.jpg"
  }
]
```

---

## 📝 Feedback System

### Submit Feedback
**POST** `/api/feedback/`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer jwt-token-here
Content-Type: application/json
```

**Body:**
```json
{
  "subject": "App Improvement Suggestion",
  "message": "I think the app could benefit from...",
  "category": "suggestion"
}
```

**Success Response (201):**
```json
{
  "message": "Feedback submitted successfully",
  "feedback": {
    "id": 701,
    "subject": "App Improvement Suggestion",
    "message": "I think the app could benefit from...",
    "category": "suggestion",
    "status": "pending",
    "created_at": "2024-02-15T12:00:00"
  }
}
```

---

## 👨‍💼 Admin Routes

### 1. Admin Login
**POST** `/api/admins/login`

**Headers:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "email": "admin@example.com",
  "password": "adminpassword"
}
```

**Success Response (200):**
```json
{
  "access_token": "admin-jwt-token-here"
}
```

### 2. Create Super Admin
**POST** `/api/admins/super-admin`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer super-admin-jwt-token
Content-Type: application/json
```

**Body:**
```json
{
  "email": "newadmin@example.com",
  "password": "adminpassword",
  "firstname": "Admin",
  "lastname": "User"
}
```

### 3. Create Admin
**POST** `/api/admins/admin`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer super-admin-jwt-token
Content-Type: application/json
```

**Body:**
```json
{
  "email": "admin@example.com",
  "password": "adminpassword",
  "firstname": "Regular",
  "lastname": "Admin"
}
```

## User Management (Admin)

### 4. Get User Profile (Admin)
**GET** `/api/admins/users/{user_id}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 5. List All Users (Admin)
**GET** `/api/admins/users`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Query Parameters:**
- `search` (optional): Search users by name or email

### 6. Deactivate User (Admin)
**PUT** `/api/admins/users/{user_id}/deactivate`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 7. Reactivate User (Admin)
**PUT** `/api/admins/users/{user_id}/reactivate`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 8. Delete User (Admin)
**DELETE** `/api/admins/users/{user_id}`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

## Resource Management (Admin)

### 9. List Resources (Admin)
**GET** `/api/admins/resources`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Query Parameters:**
- `status` (optional): Filter by status ('pending', 'approved', 'rejected')

### 10. Approve Resource (Admin)
**PUT** `/api/admins/resources/{resource_id}/approve`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 11. Reject Resource (Admin)
**PUT** `/api/admins/resources/{resource_id}/reject`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

## Event Management (Admin)

### 12. List Events (Admin)
**GET** `/api/admins/events`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Query Parameters:**
- `status` (optional): 'approved' or 'pending'

### 13. Approve Event (Admin)
**PUT** `/api/admins/events/{event_id}/approve`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 14. Reject Event (Admin)
**DELETE** `/api/admins/events/{event_id}/reject`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

## Mentorship Management (Admin)

### 15. List Mentee Applications (Admin)
**GET** `/api/admins/mentee-applications`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Query Parameters:**
- `status` (optional): Filter by application status

### 16. Approve Mentee Application (Admin)
**PUT** `/api/admins/mentee-applications/{app_id}/approve`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 17. Reject Mentee Application (Admin)
**PUT** `/api/admins/mentee-applications/{app_id}/reject`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 18. List Mentor Applications (Admin)
**GET** `/api/admins/mentor-applications`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Query Parameters:**
- `status` (optional): Filter by application status

### 19. Approve Mentor Application (Admin)
**PUT** `/api/admins/mentor-applications/{app_id}/approve`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 20. Reject Mentor Application (Admin)
**PUT** `/api/admins/mentor-applications/{app_id}/reject`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

### 21. Create Mentorship Pairing (Admin)
**POST** `/api/admins/mentorship/pairings`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
Content-Type: application/json
```

**Body:**
```json
{
  "mentor_id": 456,
  "mentee_id": 123
}
```

**Success Response (201):**
```json
{
  "message": "Mentorship pairing created successfully",
  "mentorship": {
    "id": 801,
    "mentor_id": 456,
    "mentee_id": 123,
    "status": "active",
    "created_at": "2024-02-15T13:00:00"
  }
}
```

## Feedback Management (Admin)

### 22. List All Feedback (Admin)
**GET** `/api/admins/feedback`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Query Parameters:**
- `category` (optional): Filter by feedback category
- `status` (optional): Filter by status ('pending', 'reviewed', 'resolved')

**Success Response (200):**
```json
[
  {
    "id": 701,
    "subject": "App Improvement Suggestion",
    "message": "I think the app could benefit from...",
    "category": "suggestion",
    "status": "pending",
    "user": {
      "id": 123,
      "firstname": "John",
      "lastname": "Doe"
    },
    "created_at": "2024-02-15T12:00:00"
  }
]
```

### 23. Update Feedback Status (Admin)
**PUT** `/api/admins/feedback/{feedback_id}/status`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
Content-Type: application/json
```

**Body:**
```json
{
  "status": "reviewed"
}
```

**Success Response (200):**
```json
{
  "message": "Feedback status updated successfully",
  "feedback": {
    "id": 701,
    "status": "reviewed"
    // ... other fields
  }
}
```

## Analytics & Reports (Admin)

### 24. Get Platform Summary Statistics (Admin)
**GET** `/api/admins/analytics/summary`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Success Response (200):**
```json
{
  "message": "Platform statistics retrieved successfully",
  "stats": {
    "total_users": 1500,
    "total_resources": 350,
    "total_events": 45,
    "active_mentorships": 75,
    "pending_approvals": 12,
    "monthly_signups": 150
  }
}
```

### 25. Export Users CSV (Admin)
**GET** `/api/admins/analytics/export/users.csv`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Success Response (200):**
Returns a CSV file download with user data.

### 26. Export Summary PDF Report (Admin)
**GET** `/api/admins/analytics/export/summary.pdf`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer admin-jwt-token
```

**Success Response (200):**
Returns a PDF file download with platform summary report.

## Audit Logs (Super Admin Only)

### 27. Get All Audit Logs (Super Admin)
**GET** `/api/admins/audit-logs`

**Headers:**
```
X-API-Key: your-api-key
Authorization: Bearer super-admin-jwt-token
```

**Success Response (200):**
```json
[
  {
    "id": 901,
    "admin_id": 456,
    "action": "approve_resource",
    "details": "Resource ID: 123",
    "timestamp": "2024-02-15T14:00:00",
    "admin": {
      "id": 456,
      "firstname": "Admin",
      "lastname": "User"
    }
  }
]
```

---

## 🌐 WebSocket Events (Forums)

The forums feature includes real-time messaging via WebSocket connections.

### WebSocket Connection
```javascript
import io from 'socket.io-client';

const socket = io('your-websocket-url');
```

### Join Thread Room
```javascript
socket.emit('join_thread', {
  thread_id: 501,
  user_id: 123
});
```

### Leave Thread Room
```javascript
socket.emit('leave_thread', {
  thread_id: 501,
  user_id: 123
});
```

### Listen for New Messages
```javascript
socket.on('new_message', (data) => {
  console.log('New message in thread:', data.thread_id);
  console.log('Message:', data.message);
  // Update UI with new message
});
```

### Listen for User Events
```javascript
socket.on('user_joined', (data) => {
  console.log(`User ${data.user_id} joined thread ${data.thread_id}`);
});

socket.on('user_left', (data) => {
  console.log(`User ${data.user_id} left thread ${data.thread_id}`);
});
```

---

## 🔧 Frontend Implementation Examples

### Complete Authentication Flow
```javascript
class APIClient {
  constructor(baseURL, apiKey) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
    this.token = localStorage.getItem('token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'X-API-Key': this.apiKey,
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (options.body && !(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.ok) {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        } else if (contentType && contentType.includes('text/csv')) {
          return await response.blob();
        } else if (contentType && contentType.includes('application/pdf')) {
          return await response.blob();
        }
        return await response.text();
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Request failed');
      }
    } catch (error) {
      console.error('API request failed:', error.message);
      throw error;
    }
  }

  // Authentication methods
  async register(userData) {
    const formData = new FormData();
    Object.keys(userData).forEach(key => {
      if (userData[key] !== undefined && userData[key] !== null) {
        formData.append(key, userData[key]);
      }
    });

    return this.request('/users', {
      method: 'POST',
      body: formData
    });
  }

  async login(email, password) {
    const response = await this.request('/users/login', {
      method: 'POST',
      body: { email, password }
    });
    
    if (response.access_token) {
      this.token = response.access_token;
      localStorage.setItem('token', this.token);
      localStorage.setItem('user', JSON.stringify(response.user));
    }
    
    return response;
  }

  async verifyEmail(email, otp) {
    return this.request('/users/confirm', {
      method: 'POST',
      body: { email, otp }
    });
  }

  // Resource methods
  async uploadResource(resourceData) {
    const formData = new FormData();
    Object.keys(resourceData).forEach(key => {
      if (resourceData[key] !== undefined && resourceData[key] !== null) {
        formData.append(key, resourceData[key]);
      }
    });

    return this.request('/api/resources/', {
      method: 'POST',
      body: formData
    });
  }

  async getResourcesByLevel(level) {
    return this.request(`/api/resources/level/${level}`);
  }

  // Event methods
  async getEvents() {
    return this.request('/api/events/');
  }

  async createEvent(eventData) {
    return this.request('/api/events/', {
      method: 'POST',
      body: eventData
    });
  }

  async rsvpToEvent(eventId) {
    return this.request(`/api/events/${eventId}/rsvp`, {
      method: 'POST'
    });
  }

  // Forum methods
  async getForums() {
    return this.request('/api/forums/');
  }

  async joinForum(forumId) {
    return this.request(`/api/forums/${forumId}/join`, {
      method: 'POST'
    });
  }

  async createThread(forumId, threadData) {
    return this.request(`/api/forums/${forumId}/threads`, {
      method: 'POST',
      body: threadData
    });
  }

  async sendMessage(threadId, messageData) {
    const formData = new FormData();
    Object.keys(messageData).forEach(key => {
      if (messageData[key] !== undefined && messageData[key] !== null) {
        formData.append(key, messageData[key]);
      }
    });

    return this.request(`/api/forums/threads/${threadId}/messages`, {
      method: 'POST',
      body: formData
    });
  }

  // Mentorship methods
  async applyForMentorship(applicationData) {
    return this.request('/api/mentorship/apply', {
      method: 'POST',
      body: applicationData
    });
  }

  async applyToBeMentor(applicationData) {
    return this.request('/api/mentorship/apply-mentor', {
      method: 'POST',
      body: applicationData
    });
  }

  async getMyMentorships() {
    return this.request('/api/mentorship/my-mentorships');
  }

  // Admin methods
  async adminLogin(email, password) {
    const response = await this.request('/api/admins/login', {
      method: 'POST',
      body: { email, password }
    });
    
    if (response.access_token) {
      this.token = response.access_token;
      localStorage.setItem('adminToken', this.token);
    }
    
    return response;
  }

  async getUsers(search = '') {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.request(`/api/admins/users${query}`);
  }

  async approveResource(resourceId) {
    return this.request(`/api/admins/resources/${resourceId}/approve`, {
      method: 'PUT'
    });
  }

  async getPlatformStats() {
    return this.request('/api/admins/analytics/summary');
  }
}

// Usage
const api = new APIClient('https://your-domain.com', 'your-api-key');

// Example usage in a React component
function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.login(email, password);
      console.log('Login successful:', response);
      // Redirect to dashboard or update app state
    } catch (error) {
      alert('Login failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

---

## 📊 Error Handling Reference

### Common HTTP Status Codes

**200 OK** - Request successful
```json
{
  "message": "Success message",
  "data": {...}
}
```

**201 Created** - Resource created successfully
```json
{
  "message": "Resource created successfully",
  "resource": {...}
}
```

**400 Bad Request** - Invalid request data
```json
{
  "message": "Email and password are required"
}
```

**401 Unauthorized** - Invalid credentials or missing authentication
```json
{
  "message": "Invalid credentials"
}
```

**403 Forbidden** - Insufficient permissions
```json
{
  "message": "Please confirm your email first"
}
```

**404 Not Found** - Resource not found
```json
{
  "message": "User not found"
}
```

**409 Conflict** - Resource already exists
```json
{
  "message": "This email already exists."
}
```

**500 Internal Server Error** - Server error
```json
{
  "message": "An unexpected error occurred",
  "error": "Detailed error message"
}
```

---

## 🔗 Quick Reference Summary

### Authentication Flow
1. **Get API Key**: `POST /test_generate_api_key` (or ask admin)
2. **Register**: `POST /users` → Check email for OTP
3. **Verify Email**: `POST /users/confirm` with OTP
4. **Login**: `POST /users/login` → Get JWT token
5. **Use JWT token** in `Authorization: Bearer <token>` header for protected routes

### File Upload Endpoints
- User registration: `POST /users` (profile_picture, departmental_fees)
- Resource upload: `POST /api/resources/` (file)
- Forum messages: `POST /api/forums/threads/{id}/messages` (attachment)

### Admin vs User Permissions
- **Users**: Can create resources, events, apply for mentorship, join forums
- **Admins**: Can approve resources/events, manage users, view analytics
- **Super Admins**: Can create other admins, view audit logs

### WebSocket Usage (Forums)
Connect to WebSocket, join thread rooms, listen for real-time message events

### Pagination
Some endpoints support pagination via `page` and `per_page` query parameters

---
