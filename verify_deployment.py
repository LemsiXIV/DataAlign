#!/usr/bin/env python3
"""
DataAlign v2.0 - Deployment Verification Script
Run this script in Docker environment to verify all fixes
"""

import os
import sys

def check_file_exists(file_path, description):
    """Check if a file exists and report"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} NOT FOUND")
        return False

def check_import_availability():
    """Test critical imports"""
    print("\n=== Testing Critical Imports ===")
    
    try:
        sys.path.append('/app')  # Docker path
        sys.path.append('.')     # Local path
        
        # Test encoding utilities
        from app.utils.encoding_utils import safe_read_csv, detect_csv_encoding
        print("✅ Encoding utilities import successful")
        
        # Test PDF/Excel generators  
        from app.services.generateur_pdf import GenerateurPdf
        from app.services.generateur_excel import GenerateurExcel
        print("✅ PDF/Excel generators import successful")
        
        # Test file readers
        from app.services.lecteur_fichier import read_uploaded_file
        from app.services.lecteur_fichier_optimise import LecteurFichierOptimise
        print("✅ File readers import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def check_directory_structure():
    """Verify directory structure"""
    print("\n=== Checking Directory Structure ===")
    
    base_paths = ['.', '/app']  # Local and Docker paths
    success = False
    
    for base in base_paths:
        if os.path.exists(base):
            required_files = [
                (f"{base}/app/utils/encoding_utils.py", "Encoding utilities"),
                (f"{base}/app/routes/fichiers.py", "File routes"),
                (f"{base}/app/routes/projets.py", "Project routes"),
                (f"{base}/app/routes/comparaison.py", "Comparison routes"),
                (f"{base}/app/services/lecteur_fichier.py", "File reader"),
                (f"{base}/app/services/lecteur_fichier_optimise.py", "Optimized file reader")
            ]
            
            print(f"\nChecking base path: {base}")
            all_exist = True
            for file_path, desc in required_files:
                if not check_file_exists(file_path, desc):
                    all_exist = False
            
            if all_exist:
                success = True
                break
    
    return success

def check_uploads_directory():
    """Check uploads directory structure"""
    print("\n=== Checking Uploads Directory ===")
    
    upload_paths = ['uploads', '/app/uploads']
    
    for upload_base in upload_paths:
        if os.path.exists(upload_base):
            print(f"✅ Uploads directory found: {upload_base}")
            
            # Check subdirectories
            subdirs = ['source', 'archive', 'temp']
            for subdir in subdirs:
                subdir_path = os.path.join(upload_base, subdir)
                if os.path.exists(subdir_path):
                    print(f"  ✅ {subdir} directory exists")
                else:
                    print(f"  ⚠️  {subdir} directory missing (will be created on demand)")
            return True
    
    print("❌ No uploads directory found")
    return False

def main():
    """Run all verification checks"""
    print("DataAlign v2.0 - Deployment Verification")
    print("=" * 50)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Critical Imports", check_import_availability), 
        ("Uploads Directory", check_uploads_directory)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! DataAlign v2.0 is ready for testing.")
        print("\nNext steps:")
        print("1. Upload CSV files with encoding issues")
        print("2. Test malformed CSV files (inconsistent columns)")
        print("3. Verify PDF/Excel downloads work correctly")
        print("4. Check that charts display properly")
    else:
        print("\n⚠️  Some checks failed. Please review the issues above.")
    
    return all_passed

if __name__ == "__main__":
    main()
