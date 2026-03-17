---
title: "Microsoft Patch Tuesday, March 2026 Edition"
date: 2026-03-16T09:00:00+08:00
categories: ["security"]
tags: ["auto-generated", "rss"]
draft: false
---

## 摘要

Microsoft Corp. today pushed security updates to fix at least 77 vulnerabilities in its Windows operating systems and other software. There are no pressing &#8220;zero-day&#8221; flaws this month (compared to February&#8217;s five zero-day treat), but as usual some patches may deserve more rapid attention from organizations using Windows. Here are a few highlights from this month&#8217;s Patch Tuesday.
Image: Shutterstock, @nwz.
Two of the bugs Microsoft patched today were publicly disclosed previously. CVE-2026-21262 is a weakness that allows an attacker to elevate their privileges on SQL Server 2016 and later editions.
&#8220;This isn’t just any elevation of privilege vulnerability, either; the advisory notes that an authorized attacker can elevate privileges to sysadmin over a network,&#8221; Rapid7&#8217;s Adam Barnett said. &#8220;The CVSS v3 base score of 8.8 is just below the threshold for critical severity, since low-level privileges are required. It would be a courageous defender who shrugged and deferred the patches for this one.&#8221;
The other publicly disclosed flaw is CVE-2026-26127, a vulnerability in applications running on .NET. Barnett said the immediate impact of exploitation is likely limited to denial of service by triggering a crash, with the potential for other types of attacks during a service reboot.
It would hardly be a proper Patch Tuesday without at least one critical Microsoft Office exploit, and this month doesn&#8217;t disappoint. CVE-2026-26113 and CVE-2026-26110 are both remote code execution flaws that can be triggered just by viewing a booby-trapped message in the Preview Pane.
Satnam Narang at Tenable notes that just over half (55%) of all Patch Tuesday CVEs this month are privilege escalation bugs, and of those, a half dozen were rated &#8220;exploitation more likely&#8221; &#8212; across Windows Graphics Component, Windows Accessibility Infrastructure, Windows Kernel, Windows SMB Server and Winlogon. These include:
&#8211;CVE-2026-24291: Incorrect permission assignments within the Windows Accessibility Infrastructure to reach SYSTEM (CVSS 7.8)
&#8211;CVE-2026-24294: Improper authentication in the core SMB component (CVSS 7.8)
&#8211;CVE-2026-24289: High-severity memory corruption and race condition flaw (CVSS 7.8)
&#8211;CVE-2026-25187: Winlogon process weakness discovered by Google Project Zero (CVSS 7.8).
Ben McCarthy, lead cyber security engineer at Immersive, called attention to CVE-2026-21536, a critical remote code execution bug in a component called the Microsoft Devices Pricing Program. Microsoft has already resolved the issue on their end, and fixing it requires no action on the part of Windows users. But McCarthy says it&#8217;s notable as one of the first vulnerabilities identified by an AI agent and officially recognized with a CVE attributed to the Windows operating system. It was discovered by XBOW, a fully autonomous AI penetration testing agent.
XBOW has consistently ranked at or near the top

## 来源

- [阅读原文](https://krebsonsecurity.com/2026/03/microsoft-patch-tuesday-march-2026-edition/)
- 发布时间：Wed, 11 Mar 2026 00:32:51 +0000

## 市场背景

- BTC 价格：$74,200.00
- 24h 涨跌：+3.48%

---
*自动生成于 2026-03-16T21:00:47.244837*
