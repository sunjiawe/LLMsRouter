#!/usr/bin/env python
import sys
from cli.user_management import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main()) 