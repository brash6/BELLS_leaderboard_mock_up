from setuptools import setup, find_packages

setup(
    name="BELLS_leaderboard_mock_up",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "streamlit",
        "pandas",
        "plotly",
        "openai",
        "setuptools",
        "python-dotenv",
    ],
) 