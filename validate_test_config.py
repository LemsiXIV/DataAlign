#!/usr/bin/env python3
"""
Validation script for GitLab CI test configuration
"""

import yaml

def validate_test_config():
    """Validate the test job configuration in .gitlab-ci.yml"""
    try:
        with open('.gitlab-ci.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("🔍 Validating GitLab CI test configuration...")
        
        # Check if test job exists
        if 'test' not in config:
            print("❌ Test job not found")
            return False
        
        test_job = config['test']
        
        # Check MySQL service configuration
        services = test_job.get('services', [])
        mysql_service = None
        for service in services:
            if isinstance(service, dict) and service.get('name') == 'mysql:8.0':
                mysql_service = service
                break
        
        if mysql_service:
            print("✅ MySQL 8.0 service configured")
            mysql_vars = mysql_service.get('variables', {})
            required_mysql_vars = ['MYSQL_ROOT_PASSWORD', 'MYSQL_DATABASE', 'MYSQL_USER', 'MYSQL_PASSWORD']
            for var in required_mysql_vars:
                if var in mysql_vars:
                    print(f"   ✅ {var}: {mysql_vars[var]}")
                else:
                    print(f"   ❌ Missing {var}")
        else:
            print("❌ MySQL service not properly configured")
        
        # Check database URL
        variables = test_job.get('variables', {})
        db_url = variables.get('DATABASE_URL', '')
        if 'mysql+pymysql' in db_url:
            print("✅ Database URL uses PyMySQL connector")
            print(f"   📋 URL: {db_url}")
        else:
            print(f"⚠️ Database URL might have issues: {db_url}")
        
        # Check Python dependencies in before_script
        before_script = test_job.get('before_script', [])
        mysql_deps_found = False
        pymysql_found = False
        
        for cmd in before_script:
            if 'default-libmysqlclient-dev' in cmd and 'default-mysql-client' in cmd:
                mysql_deps_found = True
                print("✅ MySQL client dependencies configured")
            if 'mysqlclient PyMySQL' in cmd:
                pymysql_found = True
                print("✅ Python MySQL connectors configured")
        
        if not mysql_deps_found:
            print("⚠️ MySQL client dependencies might be missing")
        if not pymysql_found:
            print("⚠️ Python MySQL connectors might be missing")
        
        print("\n🎯 Test configuration validation completed")
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

if __name__ == "__main__":
    validate_test_config()
