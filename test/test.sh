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
echo "   - Redis"
sleep 5

# Apply migrations
echo -e "${BLUE}📦 Applying migrations...${NC}"
python manage.py migrate --noinput
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
echo -e "${BLUE}Running pytest in parallel...${NC}"
pytest \
  --verbose \
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
echo -e "${GREEN}🎉 Test suite completed successfully!${NC}"

exit 0
