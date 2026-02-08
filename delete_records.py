"""
delete_records.py
Delete survey records from PostgreSQL database based on various criteria
Supports multiple deletion strategies:
1. By (Roll Number, School Name)
2. By School Name only
3. By (Class, Subject Group) - Subject Group is optional
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Database configuration - use Unix socket with peer authentication
DB_CONFIG = {
    "database": "smart_survey",
    "user": "postgres",
    "host": "/var/run/postgresql",
    "port": "5433"
}

def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def preview_records(cursor, where_clause, params):
    """Preview records that will be deleted"""
    preview_sql = f"""
        SELECT id, student_name, roll_number, school_name, class, subject_group
        FROM survey
        WHERE {where_clause}
    """
    cursor.execute(preview_sql, params)
    return cursor.fetchall()

def delete_by_roll_and_school(roll_number, school_name, confirm=True):
    """
    Delete records by Roll Number and School Name
    
    Args:
        roll_number: Student roll number
        school_name: School name
        confirm: If True, ask for confirmation before deletion
    """
    print("\n" + "=" * 80)
    print("🗑️  DELETE BY ROLL NUMBER AND SCHOOL NAME")
    print("=" * 80)
    print(f"Roll Number: {roll_number}")
    print(f"School Name: {school_name}")
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Preview records
    where_clause = "roll_number = %s AND school_name = %s"
    params = (roll_number, school_name)
    
    records = preview_records(cur, where_clause, params)
    
    if not records:
        print(f"\n⚠️  No records found matching criteria")
        cur.close()
        conn.close()
        return 0
    
    print(f"\n📋 Found {len(records)} record(s) to delete:")
    print("-" * 80)
    for i, rec in enumerate(records, 1):
        print(f"{i}. ID: {rec['id']}, Name: {rec['student_name']}, Roll: {rec['roll_number']}")
        print(f"   School: {rec['school_name']}, Class: {rec['class']}, Subject Group: {rec['subject_group']}")
    
    if confirm:
        print("\n" + "⚠️  WARNING: This action cannot be undone!")
        response = input("Do you want to proceed with deletion? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Deletion cancelled")
            cur.close()
            conn.close()
            return 0
    
    # Perform deletion
    delete_sql = f"DELETE FROM survey WHERE {where_clause}"
    cur.execute(delete_sql, params)
    deleted_count = cur.rowcount
    conn.commit()
    
    print(f"\n✅ Successfully deleted {deleted_count} record(s)")
    
    cur.close()
    conn.close()
    return deleted_count

def delete_by_school(school_name, confirm=True):
    """
    Delete all records from a specific school
    
    Args:
        school_name: School name
        confirm: If True, ask for confirmation before deletion
    """
    print("\n" + "=" * 80)
    print("🗑️  DELETE BY SCHOOL NAME")
    print("=" * 80)
    print(f"School Name: {school_name}")
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Preview records
    where_clause = "school_name = %s"
    params = (school_name,)
    
    records = preview_records(cur, where_clause, params)
    
    if not records:
        print(f"\n⚠️  No records found for school: {school_name}")
        cur.close()
        conn.close()
        return 0
    
    print(f"\n📋 Found {len(records)} record(s) to delete:")
    print("-" * 80)
    for i, rec in enumerate(records, 1):
        print(f"{i}. ID: {rec['id']}, Name: {rec['student_name']}, Roll: {rec['roll_number']}")
        print(f"   Class: {rec['class']}, Subject Group: {rec['subject_group']}")
    
    if confirm:
        print("\n" + "⚠️  WARNING: This will delete ALL records from this school!")
        response = input("Do you want to proceed with deletion? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Deletion cancelled")
            cur.close()
            conn.close()
            return 0
    
    # Perform deletion
    delete_sql = f"DELETE FROM survey WHERE {where_clause}"
    cur.execute(delete_sql, params)
    deleted_count = cur.rowcount
    conn.commit()
    
    print(f"\n✅ Successfully deleted {deleted_count} record(s)")
    
    cur.close()
    conn.close()
    return deleted_count

def delete_by_class_and_subject(class_name, subject_group=None, confirm=True):
    """
    Delete records by Class and optionally Subject Group
    
    Args:
        class_name: Class name (e.g., "5th", "10th")
        subject_group: Optional subject group filter
        confirm: If True, ask for confirmation before deletion
    """
    print("\n" + "=" * 80)
    print("🗑️  DELETE BY CLASS AND SUBJECT GROUP")
    print("=" * 80)
    print(f"Class: {class_name}")
    print(f"Subject Group: {subject_group if subject_group else 'Any (Not filtered)'}")
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Build query based on whether subject_group is provided
    if subject_group:
        where_clause = "class = %s AND subject_group = %s"
        params = (class_name, subject_group)
    else:
        where_clause = "class = %s"
        params = (class_name,)
    
    records = preview_records(cur, where_clause, params)
    
    if not records:
        print(f"\n⚠️  No records found matching criteria")
        cur.close()
        conn.close()
        return 0
    
    print(f"\n📋 Found {len(records)} record(s) to delete:")
    print("-" * 80)
    for i, rec in enumerate(records, 1):
        print(f"{i}. ID: {rec['id']}, Name: {rec['student_name']}, Roll: {rec['roll_number']}")
        print(f"   School: {rec['school_name']}, Class: {rec['class']}, Subject Group: {rec['subject_group']}")
    
    if confirm:
        print("\n" + "⚠️  WARNING: This action cannot be undone!")
        response = input("Do you want to proceed with deletion? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Deletion cancelled")
            cur.close()
            conn.close()
            return 0
    
    # Perform deletion
    delete_sql = f"DELETE FROM survey WHERE {where_clause}"
    cur.execute(delete_sql, params)
    deleted_count = cur.rowcount
    conn.commit()
    
    print(f"\n✅ Successfully deleted {deleted_count} record(s)")
    
    cur.close()
    conn.close()
    return deleted_count

def show_database_stats():
    """Show current database statistics"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Total records
    cur.execute("SELECT COUNT(*) FROM survey")
    total = cur.fetchone()[0]
    
    # By school
    cur.execute("""
        SELECT school_name, COUNT(*) as count 
        FROM survey 
        GROUP BY school_name 
        ORDER BY school_name
    """)
    schools = cur.fetchall()
    
    # By class
    cur.execute("""
        SELECT class, COUNT(*) as count 
        FROM survey 
        GROUP BY class 
        ORDER BY class
    """)
    classes = cur.fetchall()
    
    print("\n" + "=" * 80)
    print("📊 DATABASE STATISTICS")
    print("=" * 80)
    print(f"Total Records: {total}")
    
    print(f"\n📚 Records by School:")
    for school, count in schools:
        print(f"  • {school}: {count}")
    
    print(f"\n🎓 Records by Class:")
    for cls, count in classes:
        print(f"  • {cls}: {count}")
    
    cur.close()
    conn.close()

# ============================================================================
# INTERACTIVE MENU
# ============================================================================

def interactive_menu():
    """Interactive menu for deletion operations"""
    while True:
        print("\n" + "=" * 80)
        print("🗑️  SURVEY DATABASE - DELETE OPERATIONS")
        print("=" * 80)
        print("\nSelect deletion method:")
        print("1. Delete by Roll Number and School Name")
        print("2. Delete by School Name only")
        print("3. Delete by Class (and optionally Subject Group)")
        print("4. Show Database Statistics")
        print("5. Exit")
        print("-" * 80)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            roll_number = input("\nEnter Roll Number: ").strip()
            school_name = input("Enter School Name: ").strip()
            delete_by_roll_and_school(roll_number, school_name)
        
        elif choice == "2":
            school_name = input("\nEnter School Name: ").strip()
            delete_by_school(school_name)
        
        elif choice == "3":
            class_name = input("\nEnter Class (e.g., 5th, 10th): ").strip()
            subject_group = input("Enter Subject Group (press Enter to skip): ").strip()
            subject_group = subject_group if subject_group else None
            delete_by_class_and_subject(class_name, subject_group)
        
        elif choice == "4":
            show_database_stats()
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stats":
            show_database_stats()
        
        elif command == "roll":
            # Delete by roll number and school
            # Usage: python delete_records.py roll 300001 "JNV VARANASI"
            if len(sys.argv) >= 4:
                roll_number = sys.argv[2]
                school_name = sys.argv[3]
                delete_by_roll_and_school(roll_number, school_name, confirm=False)
            else:
                print("Usage: python delete_records.py roll <roll_number> <school_name>")
        
        elif command == "school":
            # Delete by school name
            # Usage: python delete_records.py school "JNV VARANASI"
            if len(sys.argv) >= 3:
                school_name = sys.argv[2]
                delete_by_school(school_name, confirm=False)
            else:
                print("Usage: python delete_records.py school <school_name>")
        
        elif command == "class":
            # Delete by class and optional subject group
            # Usage: python delete_records.py class "5th" "Not Applicable"
            if len(sys.argv) >= 3:
                class_name = sys.argv[2]
                subject_group = sys.argv[3] if len(sys.argv) >= 4 else None
                delete_by_class_and_subject(class_name, subject_group, confirm=False)
            else:
                print("Usage: python delete_records.py class <class_name> [subject_group]")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: stats, roll, school, class")
    
    else:
        # Run interactive menu
        interactive_menu()
