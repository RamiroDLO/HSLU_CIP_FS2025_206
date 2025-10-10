{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier-Bold;\f1\froman\fcharset0 Times-Bold;\f2\froman\fcharset0 Times-Roman;
\f3\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;}
{\*\listtable{\list\listtemplateid1\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat1\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid1\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid1}
{\list\listtemplateid2\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat1\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid101\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid2}
{\list\listtemplateid3\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat1\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid201\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid3}}
{\*\listoverridetable{\listoverride\listid1\listoverridecount0\ls1}{\listoverride\listid2\listoverridecount0\ls2}{\listoverride\listid3\listoverridecount0\ls3}}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\sa240\partightenfactor0

\f0\b\fs26 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 execute_scraping.py
\f1\fs24  \'97 The Mission Control
\f2\b0  This is the simplest file. Its only job is to start everything. It's like the "Launch" button. It sets the main goals (
\f3\fs26 TARGET_LISTINGS = 500
\f2\fs24 ) and tells the Orchestrator to begin.\

\f0\b\fs26 autoscout_orchestrator.py
\f1\fs24  \'97 The Driver & Trip Planner
\f2\b0  This is the brain of the operation. It manages the entire process from start to finish.\
\pard\tx220\tx720\pardeftab720\li720\fi-720\sa240\partightenfactor0
\ls1\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 It initializes the other components (the browser and the scraper specialist).\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 It handles the main loop: scrape a page, check if the goal is met, navigate to the next page, and repeat.\
\ls1\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 It deals with high-level tasks like handling the cookie banner and pausing between pages to avoid being blocked (
\f1\b rate limiting
\f2\b0 ).\
\pard\pardeftab720\sa240\partightenfactor0

\f0\b\fs26 \cf0 browser_scraper.py
\f1\fs24  \'97 The Advanced Car
\f2\b0  This file's only responsibility is to control the web browser.\
\pard\tx220\tx720\pardeftab720\li720\fi-720\sa240\partightenfactor0
\ls2\ilvl0\cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 It uses a special library (
\f3\fs26 undetected-chromedriver
\f2\fs24 ) to make your scraper look more like a real human user, which is crucial for avoiding detection.\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 It knows how to do basic browser actions: start, navigate to a URL, and close.\
\ls2\ilvl0\kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 It includes a very important feature: a function to detect a 
\f1\b CAPTCHA
\f2\b0  ("are you a robot?" test) and pause the script so you can solve it manually.\
\pard\pardeftab720\sa240\partightenfactor0

\f0\b\fs26 \cf0 autoscout_selenium_scraper.py
\f1\fs24  \'97 The Local Expert & Data Collector
\f2\b0  This is the specialist for the 
\f3\fs26 autoscout24.ch
\f2\fs24  website. It contains the logic that is most likely to need adjustments, and it's where you should focus your inspection.\
\pard\tx220\tx720\pardeftab720\li720\fi-720\sa240\partightenfactor0
\ls3\ilvl0
\f3\fs26 \cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 get_listings_on_page
\f2\fs24 : Knows the exact CSS selector to find all the car ads on a page.\
\ls3\ilvl0
\f3\fs26 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 extract_listing_data
\f2\fs24 : Knows how to look inside a single car ad's HTML to pull out the specific details like model, price, and mileage. 
\f1\b This is the core of your data extraction.
\f2\b0 \
\ls3\ilvl0
\f3\fs26 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 Maps_to_next_page
\f2\fs24 : Knows exactly what the "Next Page" button looks like and how to click it.\
}