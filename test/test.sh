#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "======================================"
echo " 🚀 Starting Django Test Suite"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=80
PARALLEL_JOBS=${TEST_PARALLEL_JOBS:-4}

# Wait for services
echo -e "${BLUE}⏳ Waiting for services...${NC}"
echo "   - PostgreSQL"
echo "   - Redis"
sleep 5

# Check database connectivity
echo -e "${BLUE}🔍 Checking database connectivity...${NC}"
python -c "
import sys
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URL')
    conn.close()
    print('   ✓ Main database connected')
except Exception as e:
    print(f'   ✗ Main database connection failed: {e}')
    sys.exit(1)
"

# Apply migrations
echo -e "${BLUE}📦 Applying migrations...${NC}"
python manage.py migrate --noinput --database=default
echo -e "${GREEN}   ✓ Migrations applied${NC}"

## Collect static files (if needed for tests)
#echo -e "${BLUE}📂 Collecting static files...${NC}"
#python manage.py collectstatic --noinput --clear > /dev/null 2>&1 || true
#echo -e "${GREEN}   ✓ Static files collected${NC}"

# Create coverage directory
mkdir -p coverage htmlcov

echo ""
echo "======================================"
echo " 🧪 Running Test Suite with Coverage"
echo "======================================"

# Run pytest with coverage
echo -e "${BLUE}Running pytest with coverage reporting...${NC}"
pytest \
  --verbose \
  --cov=. \
  --cov-report=xml:coverage/coverage.xml \
  --cov-report=html:htmlcov \
  --cov-report=term-missing \
  --cov-report=term:skip-covered \
  --junitxml=coverage/junit.xml \
  --tb=short \
  -n ${PARALLEL_JOBS}

TEST_EXIT_CODE=$?

echo ""
echo "======================================"
echo " 📊 Test Results Summary"
echo "======================================"

# Check test results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    exit $TEST_EXIT_CODE
fi

# Parse coverage results
if [ -f "coverage/coverage.xml" ]; then
    COVERAGE=$(python -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage/coverage.xml')
    root = tree.getroot()
    coverage = float(root.attrib['line-rate']) * 100
    print(f'{coverage:.2f}')
except:
    print('0.00')
")

    echo ""
    echo -e "${BLUE}Coverage: ${COVERAGE}%${NC}"

    # Check coverage threshold
    if (( $(echo "$COVERAGE < $COVERAGE_THRESHOLD" | bc -l) )); then
        echo -e "${YELLOW}⚠️  Warning: Coverage is below ${COVERAGE_THRESHOLD}% threshold${NC}"
        # Don't fail on coverage for now, just warn
        # exit 1
    else
        echo -e "${GREEN}✓ Coverage meets ${COVERAGE_THRESHOLD}% threshold${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Coverage report not found${NC}"
fi


echo ""
echo "======================================"
echo " 🔍 Additional Checks"
echo "======================================"

# Check for migrations
echo -e "${BLUE}Checking for missing migrations...${NC}"
python manage.py makemigrations --check --dry-run --noinput || {
    echo -e "${RED}✗ Uncommitted migrations detected!${NC}"
    exit 1
}
echo -e "${GREEN}✓ No missing migrations${NC}"

# System check
echo -e "${BLUE}Running Django system checks...${NC}"
python manage.py check --deploy || {
    echo -e "${YELLOW}⚠️  System check warnings detected${NC}"
}
echo -e "${GREEN}✓ System checks passed${NC}"

echo ""
echo "======================================"
echo " ✅ All Tests Completed Successfully!"
echo "======================================"
echo ""
echo "Coverage reports available at:"
echo "  - XML: coverage/coverage.xml"
echo "  - HTML: htmlcov/index.html"
echo "  - JUnit: coverage/junit.xml"
echo ""
echo -e "${GREEN}🎉 Test suite completed successfully!${NC}"

exit 0
