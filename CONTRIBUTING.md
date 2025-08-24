# Contributing to TaxiTracker Pro

Thank you for considering contributing to TaxiTracker Pro! We welcome contributions from developers of all skill levels.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic knowledge of Flask and web development

### Setting up Development Environment

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/TFL.git
   cd TFL
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8  # Development dependencies
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your development settings
   ```

5. **Initialize database**
   ```bash
   python app.py
   ```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use Black for code formatting: `black app.py`
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused

### Commit Messages
Follow the conventional commit format:
```
type(scope): description

feat(auth): add two-factor authentication
fix(dashboard): resolve chart loading issue
docs(readme): update installation instructions
style(ui): improve mobile responsiveness
refactor(models): simplify database queries
test(income): add unit tests for income tracking
```

### Branch Naming
- Feature branches: `feature/description-of-feature`
- Bug fixes: `bugfix/description-of-bug`
- Documentation: `docs/description-of-change`

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

### Writing Tests
- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Include edge cases and error conditions

### Test Structure
```python
def test_feature_description():
    """Test that feature works as expected."""
    # Arrange
    setup_data()
    
    # Act
    result = function_to_test()
    
    # Assert
    assert result == expected_value
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Bug Description**: Clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, browser (if applicable)
6. **Screenshots**: If applicable
7. **Log Output**: Any relevant error messages

### Bug Report Template
```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Windows 10, macOS, Ubuntu]
 - Python Version: [e.g. 3.10.0]
 - Browser: [e.g. Chrome, Firefox] (if applicable)

**Additional Context**
Add any other context about the problem here.
```

## ✨ Feature Requests

When suggesting features, please include:

1. **Feature Description**: Clear description of the feature
2. **Use Case**: Why this feature would be valuable
3. **Proposed Solution**: How you envision it working
4. **Alternatives**: Alternative solutions you've considered

## 🔄 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   pytest
   black app.py
   flake8 app.py
   ```

4. **Commit your changes**
   ```bash
   git commit -m "feat(feature): add amazing feature"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Create a Pull Request**
   - Use the PR template
   - Link any related issues
   - Add screenshots for UI changes
   - Wait for review and address feedback

### Pull Request Template
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Updated documentation

## Screenshots (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Code is commented and documented
- [ ] Tests added and passing
- [ ] No breaking changes without version bump
```

## 🏗️ Architecture Guidelines

### Database Models
- Use SQLAlchemy ORM
- Add proper relationships and constraints
- Include created_at and updated_at timestamps
- Use meaningful table and column names

### Routes and Views
- Keep routes simple and focused
- Use appropriate HTTP methods
- Implement proper error handling
- Add authentication/authorization checks

### Templates
- Use consistent HTML structure
- Follow responsive design principles
- Include proper meta tags
- Optimize for accessibility

### JavaScript
- Use modern ES6+ features
- Write modular, reusable code
- Handle errors gracefully
- Follow accessibility best practices

## 📚 Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### Tools
- [Black Code Formatter](https://black.readthedocs.io/)
- [Flake8 Linter](https://flake8.pycqa.org/)
- [Pytest Testing](https://docs.pytest.org/)

## 🤝 Community

### Communication Channels
- GitHub Issues for bugs and features
- GitHub Discussions for questions and ideas
- Email: developers@taxitracker.pro

### Code of Conduct
Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## 🏆 Recognition

Contributors are recognized in several ways:
- Listed in the project README
- GitHub contributor statistics
- Special recognition for major contributions

Thank you for helping make TaxiTracker Pro better! 🚖