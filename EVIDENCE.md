# Local build evidence

Acceptance run: 1 October 2026, Python 3.12.10, CPU only, Windows.

Installed kgdd executable: fixtures, run and Markdown report completed sequentially in 0.609 seconds measured with time.perf_counter across subprocess launches. This is a measured local runtime, not a guarantee for other machines. Fixture generation is included.

Synthetic ground truth: 200 records, 120 flagged, 80 aligned; 120 true positives, 80 true negatives, zero false positives and zero false negatives. Entered illustrative costs: 20,000 cents total, 12,000 cents on flagged activities. Independent expectation arithmetic and exact finding IDs are asserted in tests. No real trial data or measured savings are claimed.

30 pytest cases passed. Coverage includes a handwritten five-record example, empty input, malformed JSON, duplicate fields and IDs, invalid dates and costs, schema drift, Unicode and long strings, atomic write failure, corrupted labels and activity, byte determinism, provenance and all CLI subcommands.

Improvement: ambiguous duplicate JSON fields and nonfinite constants are explicitly rejected, as pinned by adversarial tests. Real-use accuracy and adoption remain unmeasured. Final expand/integrate/commercialise/maintain/kill verdict is pending the required 14-day real-use evidence window, not fabricated at build time.
