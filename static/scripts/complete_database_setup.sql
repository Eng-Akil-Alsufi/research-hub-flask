-- ===================================
-- إعداد قاعدة البيانات الكاملة
-- Research Hub Database - نسخة مبسطة
-- ===================================

-- حذف الجداول القديمة إذا كانت موجودة
DROP TABLE IF EXISTS Research_Topics;
DROP TABLE IF EXISTS ResearchPapers;
DROP TABLE IF EXISTS Students;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Supervisors;
DROP TABLE IF EXISTS Topics;
DROP TABLE IF EXISTS Departments;
DROP TABLE IF EXISTS Roles;

-- ===================================
-- 1. جدول الأدوار (Roles)
-- ===================================
CREATE TABLE Roles (
    RoleID INT AUTO_INCREMENT PRIMARY KEY,
    RoleName VARCHAR(50) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Roles (RoleID, RoleName) VALUES
(1, 'Admin'),
(2, 'Supervisor'),
(3, 'DepartmentHead'),
(4, 'Researcher');

-- ===================================
-- 2. جدول الأقسام (Departments)
-- ===================================
CREATE TABLE Departments (
    DepartmentID INT AUTO_INCREMENT PRIMARY KEY,
    DepartmentName VARCHAR(100) NOT NULL,
    Faculty VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Departments (DepartmentID, DepartmentName, Faculty) VALUES
(1, 'علوم الحاسب', 'كلية العلوم'),
(2, 'الهندسة الكهربائية', 'كلية الهندسة'),
(3, 'الرياضيات', 'كلية العلوم'),
(4, 'الفيزياء', 'كلية العلوم');

-- ===================================
-- 3. جدول المشرفين (Supervisors)
-- ===================================
CREATE TABLE Supervisors (
    SupervisorID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    AcademicRank VARCHAR(50),
    DepartmentID INT,
    FOREIGN KEY (DepartmentID) REFERENCES Departments(DepartmentID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Supervisors (SupervisorID, FirstName, LastName, Email, AcademicRank, DepartmentID) VALUES
(1, 'المهندس', 'عقيل', 'eng.amjad@university.edu', 'أستاذ مساعد', 1),
(2, 'الدكتور', 'محمد', 'dr.mohammed@university.edu', 'أستاذ مشارك', 1),
(3, 'الدكتورة', 'فاطمة', 'dr.fatima@university.edu', 'أستاذ', 2),
(4, 'الدكتور', 'أحمد', 'dr.ahmed@university.edu', 'أستاذ مساعد', 3);

-- ===================================
-- 4. جدول المستخدمين (Users) - بدون تشفير
-- ===================================
CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(100) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    RoleID INT NOT NULL,
    IsActive BOOLEAN DEFAULT TRUE,
    LastLogin DATETIME,
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Users (UserID, Username, Password, RoleID, IsActive) VALUES
(1, 'admin', 'admin123', 1, TRUE),
(2, 'المهندس.عقيل', 'password123', 2, TRUE),
(3, 'dept.head', 'password123', 3, TRUE),
(4, 'researcher1', 'pass123', 4, TRUE);

-- ===================================
-- 5. جدول الطلاب (Students)
-- ===================================
CREATE TABLE Students (
    StudentID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    EnrollmentYear INT,
    DepartmentID INT,
    FOREIGN KEY (DepartmentID) REFERENCES Departments(DepartmentID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Students (StudentID, FirstName, LastName, Email, EnrollmentYear, DepartmentID) VALUES
(1, 'سارة', 'علي', 'sara.ali@student.edu', 2023, 1),
(2, 'خالد', 'محمود', 'khaled.mahmoud@student.edu', 2022, 1),
(3, 'نورة', 'حسن', 'noura.hassan@student.edu', 2023, 2),
(4, 'عمر', 'يوسف', 'omar.youssef@student.edu', 2021, 1),
(5, 'ليلى', 'إبراهيم', 'layla.ibrahim@student.edu', 2022, 3);

-- ===================================
-- 6. جدول المواضيع البحثية (Topics)
-- ===================================
CREATE TABLE Topics (
    TopicID INT AUTO_INCREMENT PRIMARY KEY,
    TopicName VARCHAR(100) UNIQUE NOT NULL,
    Description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Topics (TopicID, TopicName, Description) VALUES
(1, 'الذكاء الاصطناعي', 'أبحاث في مجال الذكاء الاصطناعي والتعلم الآلي'),
(2, 'أمن المعلومات', 'دراسات في أمن الشبكات والبيانات'),
(3, 'تطوير الويب', 'تقنيات تطوير تطبيقات الويب الحديثة'),
(4, 'قواعد البيانات', 'أنظمة إدارة قواعد البيانات'),
(5, 'الحوسبة السحابية', 'تقنيات الحوسبة السحابية والخدمات السحابية'),
(6, 'إنترنت الأشياء', 'تطبيقات إنترنت الأشياء والأجهزة الذكية');

-- ===================================
-- 7. جدول الأبحاث (ResearchPapers)
-- ===================================
CREATE TABLE ResearchPapers (
    PaperID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    Abstract TEXT,
    PublicationYear INT,
    FilePath VARCHAR(255),
    StudentID INT,
    SupervisorID INT,
    DepartmentID INT,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (SupervisorID) REFERENCES Supervisors(SupervisorID),
    FOREIGN KEY (DepartmentID) REFERENCES Departments(DepartmentID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO ResearchPapers (PaperID, Title, Abstract, PublicationYear, FilePath, StudentID, SupervisorID, DepartmentID) VALUES
(1, 'تطبيقات الذكاء الاصطناعي في التعليم', 'دراسة شاملة حول استخدام تقنيات الذكاء الاصطناعي في تحسين العملية التعليمية', 2024, NULL, 1, 1, 1),
(2, 'أمن الشبكات اللاسلكية', 'تحليل التهديدات الأمنية في الشبكات اللاسلكية وطرق الحماية', 2023, NULL, 2, 1, 1),
(3, 'تطوير تطبيقات الويب باستخدام React', 'دراسة مقارنة لأطر عمل JavaScript الحديثة', 2024, NULL, 3, 3, 2),
(4, 'تحليل البيانات الضخمة', 'استخدام تقنيات التعلم الآلي في تحليل البيانات الضخمة', 2023, NULL, 4, 2, 1),
(5, 'الحوسبة السحابية في المؤسسات', 'دراسة فوائد وتحديات تطبيق الحوسبة السحابية', 2024, NULL, 5, 4, 3);

-- ===================================
-- 8. جدول ربط الأبحاث بالمواضيع (Research_Topics)
-- ===================================
CREATE TABLE Research_Topics (
    PaperID INT,
    TopicID INT,
    PRIMARY KEY (PaperID, TopicID),
    FOREIGN KEY (PaperID) REFERENCES ResearchPapers(PaperID) ON DELETE CASCADE,
    FOREIGN KEY (TopicID) REFERENCES Topics(TopicID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Research_Topics (PaperID, TopicID) VALUES
(1, 1),  -- الذكاء الاصطناعي
(2, 2),  -- أمن المعلومات
(3, 3),  -- تطوير الويب
(4, 1),  -- الذكاء الاصطناعي
(4, 4),  -- قواعد البيانات
(5, 5);  -- الحوسبة السحابية

-- ===================================
--  نهاية إعداد قاعدة البيانات
-- ===================================
