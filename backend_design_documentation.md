# Digitization Process Management System Backend Design

## Table of Contents
1. Introduction
2. Database Schema
3. Models
4. Architectural Patterns

---

## 1. Introduction
The Digitization Process Management System is designed to facilitate the efficient management of digitization processes for various types of documents. The backend is primarily built using modern web technologies to ensure scalability, flexibility, and maintainability.

## 2. Database Schema
The following is the database schema for the system:

- **Users**  
  - `Email` (Primary Key, String)  
  - `Name` (String)  
  - `Password` (String)  
  - `Role` (String)
  - `Note` (String)

- **Documents**  
  - `FileName` (Primary Key, String)
  - `Name` (Foreign Key, String)  
  - `BIB' (String)  
  - `CallNumber` (String)
  - `Collection' (String)
  - `PublishDate' (Integer)  
  - `FilePath` (String)  
  - `CreatedAt` (Datetime)

- **Processes Tracking**  
  - `TransactionID` (Primary Key, Integer)  
  - `FileName` (Foreign Key, String)
  - `Status` (String)  
  - `Completed_At` (Datetime)

## 3. Models

### User Model
- Email: Primary identifier and email for the user.
- Name: Full name of the user.
- Password: Secure storage of user passwords (hashed).
- Role: User role classification (Staff or Admin).
- Note: Additional notes about the user.

### Document Model
- FileName: Primary identifier for the document file.
- Name: Reference to the User who created/manages the document (Foreign Key).
- BIB: Bibliographic information of the document.
- CallNumber: Library call number for cataloging.
- Collection: Collection identifier the document belongs to.
- PublishDate: Publication date of the document (year).
- FilePath: Path to the stored document file.
- CreatedAt: Timestamp when the document was created.

### ProcessTracking Model
- TransactionID: Unique identifier for each digitization transaction.
- FileName: Reference to the Document being processed (Foreign Key).
- Status: Current status of the digitization process (e.g., Pending, Processing, Completed).
- CompletedAt: Timestamp when the process was completed.


## 4. Architectural Patterns
The backend follows a layered architecture pattern, including:
- **Presentation Layer**: Handles API requests and responses.
- **Service Layer**: Contains business logic.
- **Data Access Layer**: Manages database interactions.
  
## Conclusion
This document serves as a foundational guide for the backend design of the Digitization Process Management System. Further iterations may refine the models and structure based on requirements and feedback.
