# Code Standards

## C++ Standards

  - C++23
  - clang-tidy
  - clang-format
  - Use c/c++ standard library unless the implementation requires a better implementation for real needs.
  
## Python Standards

  - PEP
  - Black
  - Pylint

## Design Standards

- Designs originate from one or more sources. They don't happen by themselves.
- Design documentation reference relevant standards, requirements, or other causal material.
- Designs document options, but the focus is on the design not the decision process: summarize the reason for the design, not the process of litigation.
- Designs are concise. They don't repeat themselves, the statements in a design document are necessary for guiding an implementation. Designs can cause documentation but they are not user or external documentation themselves.
- Designs are persistent and not temporary. A design document also exists at a moment of time. If a design must be modified, the original design document is retired and replaced with a full new design document. Avoid fracturing of design ideas. Keep them consistent and whole and together.
- If a design uses a well known pattern, data structure or algorithm, it states the conventional name. It doesn't pretend to invent things they it did not.
- Design documents how a behavior or non-functional requirement will be met. They aren't requirements, they are not causal statements other than causing how an impolementation will happen; not why it must happen.

## Other Code Standards

 - If a standard code formatter exists for the language, the standard code formatter is used as part of the *build* process. Meaning, if a binary (executable or library) is built, before the binary is deemed acceptable, the code formatter must have run, and *all* corrections were made and includede in the binary built.
 - If a standard linter exists, the standard code linter (or "tidier") is used as part of the *build* process.
 - Code structure is clear and obvious, and **easy to read**. For example, don't use multiple levels of loops within a single function/method or implementation unit.
- Function names describe the behavior implemented 
- Implementation units adhere to the principle of single concern.
- An implementation unit is covered by one or more unit tests, and cover all branches within the implementation unit.
- If the language provides an assertion API, asserts are used for debug builds and not used for releases. Assertions are used to verify that input ranges are valid and other common best practices related to assertions. An assertion is not a unit test, i.e., an assertion doesn't make it unncessary to add a unit test. They are used for sanity checking.
- Errors are values, not exceptions. This is a decision of this project and it is understood that this may not follow conventional wisdom related to the use of exceptions for error handling.
- Favor composition over inheritance. If composition is suitable to express behavior specialization, use it. If inheritance is more natural, then use it.
- Log entry into functions/implementation units.
- Log errors at the source, not just at the receiver.
- Log the reason for an error, not the fact the error occured. E.g., "User input for name violates the expected naming pattern" and not "Error" or "Bad Input".
- Add trace logging but don't rely on it for basic problem analysis or debugging. Use "debug" logging.
- Logging at "info" level where normal operations are logged; info logging is not tracing, and generally useful for a reader to understand the basic operation of the program over a period of time.
- Warnings are warnings of possible indicators of bugs, not pedantic complaints.
- Errors are true errors and logging these errors means one or more bug exists and SHOULD/MUST be fixed. The condition(s) used to detect the error are explicitly logged as part of the error log statement.
- Memory allocators matter. Pick an allocator type appropriate for the job. Don't use malloc or `new` for everything; use it only when a different, conventionally optimal allocator isn't appropriate. Use `malloc` and `new` when it makes sense ("don't use arenas for everything").

### Code Comments

- **Explain** an implementation decision when one was made from many options (i.e., we don't explain or comment expected decisions, but from decisions that required careful consideration of alternatives).
- **Are necessary** for understanding the code being commented. Comments provide useful rationale or summarization necessary to understand the code being commented.
- **Are concise**. Comments are not used for documentation or project information tracking (e.g., a code comment pointing to a Jira ticket or Github issue).
- **Drive automated documentation**. While code documentation shouldn't be the final documentation on API, etc., for internal purposes, it should be possible to generate *Doxygen* like documentation for the benefit of project maintainers.
