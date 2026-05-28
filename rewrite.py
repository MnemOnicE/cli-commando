import re

with open("tests/test_config.py", "r") as f:
    content = f.read()

new_content = """    def test_get_thread_safety(self):
        \"\"\"Test concurrent access to the get method.\"\"\"
        config = ConfigManager()
        # Initialize with some data
        for i in range(50):
            config.set(f"key_{i}", i)

        def reader_task():
            for _ in range(100):
                # Randomly read keys, some exist, some don't
                config.get("key_25", default="fallback")
                config.get("missing_key", default="fallback")

        def writer_task():
            for i in range(50, 70):
                config.set(f"key_{i}", i)

        # Run multiple readers and writers concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 8 readers, 2 writers
            futures = []
            for _ in range(8):
                futures.append(executor.submit(reader_task))
            for _ in range(2):
                futures.append(executor.submit(writer_task))

            # Calling future.result() will propagate any exceptions with their full traceback
            for future in futures:
                future.result()
"""

content = re.sub(r'    def test_get_thread_safety\(self\):.*?self\.assertEqual\(len\(errors\), 0, f"Thread safety errors occurred: \{errors\}"\)', new_content, content, flags=re.DOTALL)

with open("tests/test_config.py", "w") as f:
    f.write(content)
