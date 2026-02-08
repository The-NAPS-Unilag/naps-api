# NAPS API Routes (Frontend Integration)

This document is generated from the current Flask route implementations in `app/routes/`.

**Base URL**
All API routes are mounted under `/api`, except the root `/` and `/health` routes.

**Auth Overview**
- JWT auth uses the `Authorization` header: `Bearer <access_token>`.
- Admin endpoints require both JWT and a valid API key header: `x-api-key: <key>`.
- Some endpoints require admin or super-admin privileges in addition to JWT.

**Public Utility**
`GET /`
Returns a simple HTML message.

`GET /health`
Health check. Returns JSON with `status`, `timestamp`, `service`, `database`. Returns 200 when DB is healthy, 503 otherwise.

**Users**
`GET /api/users/me`
Auth: JWT
Response: current user (serialized by `UserSchema`) or 404.

`GET /api/users`
Auth: JWT
Query: `page` (int, default 1), `per_page` (int, default 10)
Response: `{ users: [...], total, pages, current_page }`

`POST /api/users`
Auth: none
Consumes: `multipart/form-data`
Required form fields: `firstname`, `lastname`, `email`, `current_level`, `matric_no`, `password`
Optional files: `departmental_fees`, `profile_picture`
Response: new user or error.
Notes: Uploads files to Cloudinary if present.

`POST /api/users/confirm`
Auth: none
Body: JSON `{ email, otp }`
Response: whatever `confirm_user_email` returns.

`POST /api/users/resend-otp`
Auth: none
Body: JSON `{ email }`
Response: resend status or 404 if user not found.

`POST /api/users/login`
Auth: none
Body: JSON `{ email, password }`
Response: `{ access_token, user }` or 401.
Notes: Rejects if email not confirmed.

`POST /api/users/login/matric`
Auth: none
Body: JSON `{ matric_no, password }`
Response: `{ access_token, user }` or 401.

`GET /api/users/<user_id>/activity`
Auth: JWT (self or admin)
Query: `limit` (int, default 20), `offset` (int, default 0)
Response: `{ activities: [{ id, action, description, created_at }] }`

`PUT /api/users/update/<user_id>`
Auth: JWT
Consumes: `multipart/form-data`
Required: user must match JWT identity.
Body fields: `current_level` (optional), `bio` (optional), `profile_picture` (file, optional)
Response: `{ message: 'Edited Successful' }`

`POST /api/users/forgot-password`
Auth: none
Body: JSON `{ email }`
Response: whatever `initiate_password_reset` returns.

`POST /api/users/reset-password`
Auth: none
Body: JSON `{ email, otp, new_password }`
Response: whatever `reset_password` returns.

`DELETE /api/users/delete/<user_id>`
Auth: JWT
Required: user must match JWT identity.
Response: `{ message: 'Delete Successful' }`

**API Key Management**
`POST /api/generate_api_key`
Auth: JWT + Admin
Response: `{ message, api_key }`

`POST /api/test_generate_api_key`
Auth: none
Response: `{ message, api_key }`
Notes: Marked as unsafe in code comment.

`GET /api/api_keys`
Auth: JWT + Admin
Response: list of API keys.

`DELETE /api/api_keys/<api_key_id>`
Auth: JWT + Admin
Response: `{ message }`

**Admins**
All `/api/admins/*` routes require `x-api-key` + JWT unless noted.

`POST /api/admins/login`
Auth: `x-api-key` only
Body: JSON `{ email, password }`
Response: `{ access_token }` or 401.

`POST /api/admins/super-admin`
Auth: `x-api-key` + JWT + Super Admin
Body: JSON `{ email, password, firstname, lastname }`
Response: `{ message, user_id }`

`POST /api/admins/admin`
Auth: `x-api-key` + JWT + Super Admin
Body: JSON `{ email, password, firstname, lastname }`
Response: `{ message, user_id }`

`GET /api/admins/users/<user_id>`
Auth: `x-api-key` + JWT + Admin
Response: user profile or 404.

`GET /api/admins/users`
Auth: `x-api-key` + JWT + Admin
Query: `search` (optional)
Response: list of users.

`PUT /api/admins/users/<user_id>/deactivate`
Auth: `x-api-key` + JWT + Admin
Response: `{ message }`

`PUT /api/admins/users/<user_id>/reactivate`
Auth: `x-api-key` + JWT + Admin
Response: `{ message }`

`DELETE /api/admins/users/<user_id>`
Auth: `x-api-key` + JWT + Admin
Response: `{ message }`

`GET /api/admins/resources`
Auth: `x-api-key` + JWT + Admin
Query: `status` (optional)
Response: list of resources.

`PUT /api/admins/resources/<resource_id>/approve`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, resource }`

`PUT /api/admins/resources/<resource_id>/reject`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, resource }`

`GET /api/admins/events`
Auth: `x-api-key` + JWT + Admin
Query: `status` = `approved` or `pending` (optional)
Response: list of events.

`PUT /api/admins/events/<event_id>/approve`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, event }`

`DELETE /api/admins/events/<event_id>/reject`
Auth: `x-api-key` + JWT + Admin
Response: `{ message }`

`GET /api/admins/mentee-applications`
Auth: `x-api-key` + JWT + Admin
Query: `status` (optional)
Response: list of mentee applications.

`PUT /api/admins/mentee-applications/<app_id>/approve`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, application }`

`PUT /api/admins/mentee-applications/<app_id>/reject`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, application }`

`GET /api/admins/mentor-applications`
Auth: `x-api-key` + JWT + Admin
Query: `status` (optional)
Response: list of mentor applications.

`PUT /api/admins/mentor-applications/<app_id>/approve`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, application }`

`PUT /api/admins/mentor-applications/<app_id>/reject`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, application }`

`POST /api/admins/mentorship/pairings`
Auth: `x-api-key` + JWT + Admin
Body: JSON `{ mentor_id, mentee_id }`
Response: `{ message, mentorship }`

`GET /api/admins/feedback`
Auth: `x-api-key` + JWT + Admin
Query: `category` (optional), `status` (optional)
Response: list of feedback entries.

`PUT /api/admins/feedback/<feedback_id>/status`
Auth: `x-api-key` + JWT + Admin
Body: JSON `{ status }`
Response: `{ message, feedback }`

`GET /api/admins/analytics/summary`
Auth: `x-api-key` + JWT + Admin
Response: `{ message, stats }`

`GET /api/admins/analytics/export/users.csv`
Auth: `x-api-key` + JWT + Admin
Response: CSV file download.

`GET /api/admins/analytics/export/summary.pdf`
Auth: `x-api-key` + JWT + Admin
Response: PDF file download.

`GET /api/admins/audit-logs`
Auth: `x-api-key` + JWT + Super Admin
Response: list of audit logs.

**Events**
Base path: `/api/events`

`GET /api/events/`
Auth: JWT
Response: list of approved events.

`GET /api/events/<event_id>`
Auth: JWT
Response: event detail.

`POST /api/events/`
Auth: JWT
Body: JSON `{ name, description, date, time, location, event_type, capacity, image_url? }`
Or: `multipart/form-data` with fields `name`, `description`, `date`, `time`, `location`, `event_type`, `capacity` and optional file `image`
Notes: `date` is ISO date (`YYYY-MM-DD`), `time` is `HH:MM`.
Notes: If `image` is provided, it is uploaded to Cloudinary and stored as `image_url`.
Response: `{ id, name, message }`

`POST /api/events/<event_id>/rsvp`
Auth: JWT
Response: `{ event_id, message }`

`POST /api/events/<event_id>/cancel_rsvp`
Auth: JWT
Response: `{ event_id, message }`

`GET /api/events/user-rsvps`
Auth: JWT
Response: `{ events: [<event>] }`

`GET /api/events/type/<event_type>`
Auth: JWT
Response: list of events filtered by type.

Event fields include: `image_url`, `user_has_rsvpd`.

**Resources**
Base path: `/api/resources`

`POST /api/resources/`
Auth: JWT
Consumes: `multipart/form-data`
Required form fields: `title`, `author`, `course_title`, `level`
Required file: `file`
Optional form fields: `contributors` (repeatable)
Response: `{ message, resource }`

`GET /api/resources/level/<level>`
Auth: JWT
Response: list of approved resources for a level.

Resource fields include: `file_type`, `file_size`, `status`, `is_approved`.
Notes: `file_type` and `file_size` are derived at upload time and may be `null` if unavailable.

`GET /api/resources/pending`
Auth: JWT + Admin
Response: list of pending resources.

`POST /api/resources/<resource_id>/approve`
Auth: JWT + Admin
Response: `{ message, resource }`

`DELETE /api/resources/<resource_id>`
Auth: JWT + Admin
Response: `{ message }`

**Forums**
Base path: `/api/forums`

`GET /api/forums/`
Auth: none
Response: list of forums.

`POST /api/forums/`
Auth: JWT + Admin
Body: JSON `{ name, description, is_general? }`
Response: `{ message, forum }`

`POST /api/forums/<forum_id>/join`
Auth: JWT
Response: `{ message }`

`POST /api/forums/<forum_id>/threads`
Auth: JWT
Body: JSON `{ title, body }`
Response: `{ message, thread }`

`GET /api/forums/threads/<thread_id>`
Auth: JWT
Response: `{ thread, messages }`

`POST /api/forums/threads/<thread_id>/messages`
Auth: JWT
Consumes: `multipart/form-data`
Required form field: `content`
Optional file: `attachment`
Optional form field: `parent_message_id`
Response: `{ message, message }`
Notes: Emits Socket.IO event `new_message` to room `thread_<thread_id>`.

`GET /api/forums/explore`
Auth: none
Response: list of forums.

`GET /api/forums/recommended`
Auth: none
Response: list of recommended forums.

`GET /api/forums/top-contributors`
Auth: none
Response: list of user summaries.

`GET /api/forums/threads/<thread_id>/messages`
Auth: none
Response: list of messages in a thread.

`POST /api/forums/messages/<message_id>/like`
Auth: JWT
Response: `{ message, likes }`

**Socket.IO Events**
`join_thread`
Client emits: `{ thread_id, user_id }`
Server emits: `user_joined` to room `thread_<thread_id>`.

`leave_thread`
Client emits: `{ thread_id, user_id }`
Server emits: `user_left` to room `thread_<thread_id>`.

**Mentorship**
Base path: `/api/mentorship`

`POST /api/mentorship/apply`
Auth: JWT
Body: JSON `{ matric_no, level, areas_of_interest }`
Response: `{ message, application }`

`POST /api/mentorship/apply-mentor`
Auth: JWT
Body: JSON `{ academic_background, area_of_expertise?, preferred_mode, phone_no?, areas_of_interest?, current_level? }`
Notes: `phone_no` is optional. If `area_of_expertise` is not provided, `current_level` is used as fallback.
Response: `{ message, application }`

`GET /api/mentorship/applications`
Auth: JWT + Admin
Response: list of pending mentee applications.

`GET /api/mentorship/mentor-applications`
Auth: JWT + Admin
Response: list of pending mentor applications.

`POST /api/mentorship/mentor-applications/<application_id>/approve`
Auth: JWT + Admin
Response: `{ message, application }`

`POST /api/mentorship/mentor-applications/<application_id>/reject`
Auth: JWT + Admin
Body: JSON `{ reason }`
Response: `{ message, application }`

`POST /api/mentorship/assign-mentor`
Auth: JWT + Admin
Body: JSON `{ mentorship_application_id, mentor_id }`
Response: `{ message, mentorship }`

`POST /api/mentorship/schedule-session`
Auth: JWT
Body: JSON `{ mentorship_id, scheduled_time, duration, notes? }`
Notes: `scheduled_time` must be ISO format.
Response: `{ message, session }`

`POST /api/mentorship/submit-feedback`
Auth: JWT
Body: JSON `{ session_id, rating, comments? }`
Response: `{ message, feedback }`

`GET /api/mentorship/my-mentorships`
Auth: JWT
Response: `{ as_mentor: [...], as_mentee: [...] }`
Notes: Each mentorship object includes `area_of_expertise` when available.

`GET /api/mentorship/mentorships/<mentorship_id>/sessions`
Auth: JWT
Response: list of sessions. Requires requester to be mentor or mentee in this mentorship.

`POST /api/mentorship/mentorships/<mentorship_id>/complete`
Auth: JWT
Response: `{ message, mentorship }`
Notes: Only mentor or admin can complete.

**Feedback**
Base path: `/api/feedback`

`POST /api/feedback/`
Auth: JWT
Body: JSON `{ subject, message, category? }`
Response: `{ message, feedback }`
