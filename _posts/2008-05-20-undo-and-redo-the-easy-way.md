---
layout: single
title: Undo and Redo the "Easy" Way
date: 2008-05-20 11:02:06.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Code
tags: []
meta:
  spaces_8e963f1d044baa6ea177d10f0c6ccc02_permalink: http://cid-f610c86c6d82b8a2.users.api.live.net/Users(-715851972732602206)/Blogs('F610C86C6D82B8A2!116')/Entries('F610C86C6D82B8A2!196')?authkey=bau8ZqLz*pg%24
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2008/05/20/undo-and-redo-the-easy-way/"
---

<div id="msgcns!F610C86C6D82B8A2!196" class="bvMsg">

<div>

<http://www.codeproject.com/KB/cpp/transactions.aspx>

</div>

<div>

 

</div>

<div>

<table data-cellspacing="0" data-cellpadding="0" data-border="0">
<colgroup>
<col style="width: 50%" />
<col style="width: 50%" />
</colgroup>
<tbody>
<tr data-valign="top">
<td colspan="2"><table data-cellspacing="0" data-cellpadding="0" data-border="0">
<tbody>
<tr>
<td><a href="http://nsclass.spaces.live.com/"></a></td>
<td style="text-align: right;" width="100%"></td>
</tr>
<tr>
<td colspan="2"></td>
</tr>
<tr>
<td colspan="2"></td>
</tr>
</tbody>
</table></td>
</tr>
<tr>
<td colspan="2" data-valign="top"><span></span>
<table data-cellspacing="0" data-cellpadding="3" width="100%" data-border="0">
<colgroup>
<col style="width: 50%" />
<col style="width: 50%" />
</colgroup>
<tbody>
<tr data-valign="top">
<td><a href="http://nsclass.spaces.live.com/script/Content/Chapter.aspx?chptId=5"><u>Languages</u></a> » <a href="http://nsclass.spaces.live.com/KB/cpp/"><u>C / C++ Language</u></a> » <a href="http://nsclass.spaces.live.com/KB/cpp/index.aspx?#C%20/%20C++%20Language%20-%20General"><u>General</u></a> <span>    Intermediate</span> <span></span>
<h1 id="undo-and-redo-the-easy-way"><span>Undo and Redo the "Easy" Way</span></h1>
<p><strong>By <a href="http://nsclass.spaces.live.com/script/Articles/MemberArticles.aspx?amid=49251"><u>compiler</u></a></strong></p>
<p><span>This article introduces a simple approach to in-memory transactions that can be used to implement Undo and Redo. The technique uses SEH and Virtual Memory and requires only STL and Win32.</span></p></td>
<td style="width: 210px"><span>VC6, VC7, VC7.1, C++Windows, NT4, Win2K, WinXP, STL, VS.NET2003, VS, Dev</span>
<p><span style="padding-right:2ex;">Posted</span>: <strong>3 Oct 2002</strong><br />
<span style="padding-right:.5ex;">Updated</span>: <strong>20 Jun 2004</strong><br />
<span style="padding-right:3.2ex;">Views</span>: <strong>113,984</strong></p></td>
</tr>
<tr>
<td colspan="2"><table width="100%">
<tbody>
<tr>
<td></td>
<td style="text-align: right; white-space: nowrap;"></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

<div>

</div>

</div>

</div>

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr>
<td><table>
<colgroup>
<col style="width: 50%" />
<col style="width: 50%" />
</colgroup>
<tbody>
<tr>
<td style="text-align: right; white-space: nowrap;"><span>43 votes for this Article.</span></td>
<td><table data-cellspacing="0" data-cellpadding="0" data-border="1">
<tbody>
<tr>
<td width="20" data-bgcolor="white" height="7"><img src="http://nsclass.spaces.live.com/script/Ratings/Images/red.gif" data-align="center" data-border="0" width="20" height="7" /></td>
<td width="20" data-bgcolor="white" height="7"><img src="http://nsclass.spaces.live.com/script/Ratings/Images/red.gif" data-align="center" data-border="0" width="20" height="7" /></td>
<td width="20" data-bgcolor="white" height="7"><img src="http://nsclass.spaces.live.com/script/Ratings/Images/red.gif" data-align="center" data-border="0" width="20" height="7" /></td>
<td width="20" data-bgcolor="white" height="7"><img src="http://nsclass.spaces.live.com/script/Ratings/Images/red.gif" data-align="center" data-border="0" width="20" height="7" /></td>
<td width="20" data-bgcolor="white" height="7"><img src="http://nsclass.spaces.live.com/script/Ratings/Images/red.gif" data-align="center" data-border="0" width="11" height="7" /></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

[<u>Popularity: 7.41</u>](http://nsclass.spaces.live.com/script/Articles/TopArticles.aspx?ta_so=1 "Calculated as rating x Log10(# votes)") Rating: **4.53** out of 5

<div>

<table>
<colgroup>
<col style="width: 20%" />
<col style="width: 20%" />
<col style="width: 20%" />
<col style="width: 20%" />
<col style="width: 20%" />
</colgroup>
<tbody>
<tr>
<td><img src="http://nsclass.spaces.live.com/script/Ratings/Images/pollcol.gif" title="3 votes, 8.8%" data-border="0" width="10" height="2" alt="3 votes, 8.8%" /><br />
1</td>
<td><img src="http://nsclass.spaces.live.com/script/Ratings/Images//Images/t.gif" title="0 votes, 0.0%" data-border="0" width="10" height="1" alt="0 votes, 0.0%" /><br />
2</td>
<td><img src="http://nsclass.spaces.live.com/script/Ratings/Images//Images/t.gif" title="1 vote, 2.9%" data-border="0" width="10" height="1" alt="1 vote, 2.9%" /><br />
3</td>
<td><img src="http://nsclass.spaces.live.com/script/Ratings/Images//Images/t.gif" title="1 vote, 2.9%" data-border="0" width="10" height="1" alt="1 vote, 2.9%" /><br />
4</td>
<td><img src="http://nsclass.spaces.live.com/script/Ratings/Images/pollcol.gif" title="29 votes, 85.3%" data-border="0" width="10" height="20" alt="29 votes, 85.3%" /><br />
5</td>
</tr>
</tbody>
</table>

</div>

\

<div>

- [<u>Download source - 51 Kb</u>](http://nsclass.spaces.live.com/mmm2008-05-08_20.17/transactions/Transactions_src.zip)
- [<u>Download demo project - 59 Kb</u>](http://nsclass.spaces.live.com/mmm2008-05-08_20.17/transactions/Transactions_demo.zip)
- [<u>Download MFC SDI demo project - 87 Kb</u>](http://nsclass.spaces.live.com/mmm2008-05-08_20.17/transactions/Transactions_mfc_demo.zip)
- [<u>Download MFC MDI demo project - 114 Kb</u>](http://nsclass.spaces.live.com/mmm2008-05-08_20.17/transactions/Transactions_mfc_mdi_demo.zip)
- [<u>Download all the above plus binaries - 593 KB</u>](http://nsclass.spaces.live.com/mmm2008-05-08_20.17/transactions/Transactions_complete.zip)

 

## Introduction

This article reviews some other CodeProject articles on implementing Undo/Redo and introduces a new approach using structured exception handling and virtual memory protection. The approach is small, very high performance and features a good enforcement policy (it's easy to use correctly, and hard to use incorrectly). The working principles may be somewhat difficult to understand, but the advantages it offers in speed and reduced programming effort overwhelm the disadvantages.

Since implementing Undo/Redo functionality (aka. transactions) is rarely an easy thing to do, and can become very difficult as an application grows in complexity, it is rarely done well. Applications that support add-ins (third-party extensions) have a particularly bad time of it. Too often the functionality is limited, buggy, and onerous for developers to support.

There are a handful of other articles on CodeProject discussing Undo/Redo, and suggesting implementation strategies. This article introduces one more approach – one that may save you a lot of coding and result in higher-performance applications.

## Previous work

Yingle Jia’s article [<u>A Basic Undo/Redo Framework for C++</u>](http://www.codeproject.com/cpp/undoredo_cpp.asp) employs a straightforward procedural approach. Jia proposes a `Command` class with semantic `Execute` and `UnExecute` methods. The responsibility to implement these methods in a manner appropriate for the application falls on client developers. For example, to properly handle memory management Jia suggests a reference counting implementation, that keeps objects in memory after they have been semantically “deleted”. Implementing `Execute` and `Unexecute` can be non-trivial. For example, to avoid redundant duplication, the developer must be careful to capture only the minimally sufficient information (only what changed). This is what I call semantic, or procedural undo.

Keith Rule’s [<u>Simple and Easy Undo/Redo</u>](http://www.codeproject.com/docview/undo.asp) certainly lives up to its title. Rule makes use of lists of `CMemFile` objects to capture serialized versions of the document, before each undoable action. Any state in the undo history can be recovered by reading the contents of the appropriate `CMemFile`, assuming the `CDocument` has implemented serialization. Rule’s use of Mix-ins makes integration of his code very easy for existing MFC applications. This is what I call state-capture.

Jen Nilsson’s [<u>Undo Manager</u>](http://www.codeproject.com/atl/undomgr.asp) provides an interesting look at integrating with the OLE framework for undo/redo using ATL. The OLE framework is conceptually similar to Jia’s procedural approach, but adds cross application undo semantics (e.g. for OLE embeddings).

Tom Morris provides an interesting tutorial on implementing Undo/Redo through state-capture in [<u>Implementing Undo / Redo - The DocVars Method</u>](http://www.codeproject.com/docview/undoredo_demo.asp). His approach is conceptually similar to Rule's, but focuses on internal document data structures rather than the document itself. The primary advantage of Morris' approach is that the document is able to contain and persist a sequence of document states, which allows undo and redo operations to span editing sessions. That is, it becomes possible to undo the last operation performed, before closing a document, after the document had been reopened (potentially by someone other than the original editor). A nice feature, indeed. I call this persistent undo.

## Motivation

All of the above articles assume the use of one class library or another (MFC, ATL, STL, etc.), and Nilsson also depends on runtime support for OLE. Each requires modifications to the application's data representation classes (the document itself or discreet objects within the document), and/or operations. I was interested in an approach that could be used in pure Win32 code bases and did not require the modification of any interanl data structures or data manipulation code.

Another drawback of Jia and Nilsson is requiring objects to remain in memory after semantic removal, thus adding constraints on behavior as well as added memory overhead (it’s assumed that “deleted” objects should not interact with other objects in memory or continue processing events, for example). It can be very hard to ensure these rules are followed in all but trivial applications.

Rule places fewer constraints on behavior (other than serialization) but duplicates entire serialized documents repeatedly, thus trading simplicity for performance and memory overhead. Morris' approach features similar memory overhead due to duplication of document data.

In addition to constraints placed on the developer, the scalability of the procedural and serialization based approaches is questionable. Certainly, Rule cannot continue to operate when document size exceeds 50% of available memory (compression of backup `CMemFiles` improves the situation somewhat). Jia and Nilsson don’t duplicate as much data (assuming an efficient implementation), but the reference counting approach does result in objects remaining in memory after having been “deleted” and may require additional logic to “disconnect” those objects from other data structures. Morris requires a duplicate set of document data to be created before each edit, thus adding to memory and processing overhead.

It is important to consider the "enforcement policy" of each of these techniques. That is, how many ways are there to inadvertly break the system and introduce bugs? All of the above techniques require some faith that developers have been educated in the proper use of the system and understand its use and limitations. I've found that a stretch of reason, regardless of best intentions.

Finally, in cases where an application uses data elements from outside libraries it may not be possible to implement the above techniques without some difficulty. For example, a graph analysis toolkit may include data objects that reference each other via pointers. Since it is unlikely that these classes will be based on MFC, they won’t support Rule’s serialization based approach. Likewise, adding the semantic behavior required by Jia and Nilsson may be unattainable. Hence, it is imperative that a general-purpose undo framework NOT require modification to existing data object classes.

Finally, portability of MFC and COM based solutions is questionable.

## Summary of the new approach

The state of a program at any given moment is strictly defined by the state of the sequence of digital memory representing that application – obvious, eh? It's humbling to remember that the code we create does nothing more than twiddle bits on a chip somewhere. However, this observation also presents us with an opportunity: If we could detect the changes made to our applications’ memory, and record them, then we’d have a good chance of reversing and replaying them at our whim.

That is the basic premise of this system – to detect changes to memory and record them at the binary level, then reverse them and play them back as required to restore a given state of the application.

This approach has several advantages, which should become apparent after reading through the code:

1.  The **decoupling of data objects from the undo/redo implementation** . No changes to objects that will participate in transactions are required. No extra code is required to capture object state. No extra code is required in object manipulation functions.
2.  **Very low memory overhead.** By recording compressed changes in memory state this approach captures a minimum of information.
3.  **Very high runtime performance.**
    1.  Undo and Redo operations are implemented by sequentail binary operations on memory. These operations are very low effort, can be accelerated in many new processors (e.g. MMX), and can be parallelized at the page level.
    2.  Transaction effort (capturing and replaying) scales predominantly with the amount of data changed, not the size of the data as a whole.

**Real transactions.** The transactions are atomic, consistent, occur in isolation and are durable (giving some leeway to the fact this approach runs only in memory).

**Data safety.** Because application data is write-protected outside of transactions, any attempt to change the data outside transaction will result in an exception. This makes it very easy to identify code that is “misbehaving” and correct it. Even outside a transaction, however, data access is allowed unimpeded.

**Simple API.** There are only a handful or methods in the API, most with zero or one parameter.

Some drawbacks include:

1.  **Narrow focus.** This technique won’t provide a complete undo/redo framework for most applications (but for many, it will). Because many operations don’t involve memory across processes and media (creating a new window, file or registry entry for example) it will be necessary to wrap this code with a system such as Jia’s that handles non-memory based operations with procedural methods.
2.  **Opaqueness.** The direct manipulation of object representations without execution of object code is a foreign concept to most developers and may be difficult to fully grasp. It sometimes leads to interesting and challenging bugs.

## Implementation

Wow. Just past the introduction and this article is already too long. I will try to be brief, but there is a lot to be explained here. My goal for this article was an implementation with minimal dependencies on outside code libraries, but in practice I found STL very useful. I chose to spurn MFC, WTL and ATL but make use of STL for expediency and code readability. The result is a very simple system that can be used with MFC and ATL projects as well as pure Win32 code bases.

It is also portable to POSIX platforms with extended SIG_INFO structures containing data pointers for read/write violations (e.g. Linux 2.4+ kernel). Most platforms support this since it is generally needed to do copy-on-write for dynamically loaded shared objects (DLLs).

### SEH: Just in Time Write Detection

Windows includes a facility to detect attempts to change memory and respond to them via Structured Exception Handling (SEH). The `_try {} _except() {}` block allows us to catch exceptions and pass them through a filter we supply:

    int ExceptionFilter(LPEXCEPTION_POINTERS e);

    int main()
    {
        int retval = 0;
        __try {
                retval = DoWork();
        } __except(ExceptionFilter(GetExceptionInformation())) {
                printf("Opps, we have a problem...\n");
        };

        return retval;
    }

Using this facility, we can detect when a memory protection fault occurs, and what memory was in question:

    int ExceptionFilter(LPEXCEPTION_POINTERS e)
    {
        // we are only interested in access violations (memory faults)
        if (e->ExceptionRecord->ExceptionCode != EXCEPTION_ACCESS_VIOLATION)
            return EXCEPTION_CONTINUE_SEARCH;

        // the exception information includes the type of access (read
        // or write), and the address of the fault
        bool writing = (e->ExceptionRecord->ExceptionInformation[0] != 0);
        void* addr = (void*)e->ExceptionRecord->ExceptionInformation[1];

        // TODO: okay, now what?
             
        return EXCEPTION_CONTINUE_EXECUTION;
    }

The exception filter may return one of three values:

- `EXCEPTION_CONTINUE_SEARCH` indicates that the filter has taken no action on the exception, and that propagation should continue to other handlers (in the case of nested `try` statements).
- `EXCEPTION_CONTINUE_EXECUTION` indicates that the filter has taken action to resolve the exception, and that execution should continue at the point of the exception.
- An option we don’t use here.

This is great, but we generally aren’t involved in deciding what memory our application can read and write. For obvious reasons, the OS generally takes care of that for us. If we allocate a chunk of memory using `new` or `malloc`, it is automatically read and write enabled and our filter will never get called. Thankfully, Windows’ virtual memory functions provide a way for us to explicitly control the permissions of memory we allocate.

## Virtual Memory: Page Protection and Management

Win32 virtual memory functions can allocate, protect and de-allocate blocks of addresses in the virtual memory space. See MSDN for more information on `VirtualAlloc`, `VirtualProtect` and `VirtualFree`.

We can allocate memory via `VirtualAlloc` and then set the protection to `PAGE_READONLY` using `VirtualProtect`. Any attempt to write to that memory will generate an access violation that will be passed to our exception filter. In `ExceptionFilter`, we can check to see address is on a page we manage, and if so do the following:

1.  Make a copy of the page
2.  Set the protection of the copy to `PAGE_READONLY`
3.  Set the protection of the original to `PAGE_READWRITE`
4.  Return `EXCEPTION_CONTINUE_EXECUTION`

Returning `EXCEPTION_CONTINUE_EXECUTION` from the filter allows the code performing the memory access to continue to operate as if nothing has happened. Meanwhile, we made a copy of the page to save its state before any changes. This technique is often called “copy on write”, and you can read more about it <a href="http://www.google.com/search?hl=en&amp;ie=UTF-8&amp;oe=UTF-8&amp;q=copy+on+write" target="_blank"><u>elsewhere on the web</u></a>.

To track which pages we manage, we need some simple data structures:

    typedef std::vector<void*> Pages;
    typedef std::map<void*, void*> PageMap;

    static Pages pages;
    static PageMap backups;

Each time we allocate a page, we add it to `pages`. Each backup we make is added to `backups` with a pointer to the original page as the key. With these structures in place, the implementation of the exception filter starts to take form:

    int ExceptionFilter(LPEXCEPTION_POINTERS e)
    {    
        if (e->ExceptionRecord->ExceptionCode != EXCEPTION_ACCESS_VIOLATION)
            return EXCEPTION_CONTINUE_SEARCH;

        bool writing = (e->ExceptionRecord->ExceptionInformation[0] != 0);
        void* addr = (void*)e->ExceptionRecord->ExceptionInformation[1];
        void* page = (void*)((unsigned long)addr & ~(PAGE_SIZE - 1));

        Pages::iterator i = std::find(pages.begin(), pages.end(), page);
        if (i == pages.end())
            return EXCEPTION_CONTINUE_SEARCH;

        void* backup = ::VirtualAlloc(0, PAGE_SIZE, MEM_COMMIT, PAGE_READWRITE);
        memcpy(backup, page, PAGE_SIZE);
        backups[page] = backup;

        DWORD old = 0;
        BOOL ok = FALSE;
        ok = ::VirtualProtect(backup, PAGE_SIZE, PAGE_READONLY, &old);
        if (ok == FALSE)
            return EXCEPTION_CONTINUE_SEARCH;

        ok = ::VirtualProtect(page, PAGE_SIZE, PAGE_READWRITE, &old);
        if (ok == FALSE)
            return EXCEPTION_CONTINUE_SEARCH;

        return EXCEPTION_CONTINUE_EXECUTION;
    }

Excellent!

However, we still have a problem: Windows’ virtual memory functions only deal with page-sized chunks (4096 bytes). To make things useful in the general case, we need a memory manger that operates on chunks of memory from `VirtualAlloc`. Fortunately, that problem has been solved before. The source code includes a *very* simple memory manager that can slice arbitrarily sized allocations from chunks of virtual memory. See the API functions `Allocate` and `Deallocate`. If you need a more industrial strength solution, see <a href="http://groups.google.com/groups?hl=en&amp;lr=lang_en&amp;ie=UTF-8&amp;oe=UTF-8&amp;safe=off&amp;q=fast+memory+allocation+algorithm&amp;btnG=Google+Search" target="_blank"><u>google</u></a>. Punt.

## Houston, we have Undo

Now we can detect changes to memory and make copies of only the memory being changed. This is great stuff, eh? Say we have a gazillion bytes allocated but will only be changing a few in any given transaction. Using this technique, we only have to copy the pages where the changes are made, and the code that makes the changes doesn’t even need to know we’re doing it.

To reverse the changes we need only copy the backup pages over the top of the target pages. Very cool, eh? Unfortunately, at this point we can’t Redo the Undo since we aren’t keeping a copy of the page *after* the changes. Hmmm. Another drawback with this technique is that we copy the entire page, even when a subset of the page is changed. This is a bit wasteful. To do better we could compress the backup, but we can do better than that using some XOR tricks and get Redo too.

## XOR Tricks: Recording Changes and Redo

Rather than go into a discussion of XOR and its many uses, I’ll refer you to Daniel Turini’s excellent [<u>article</u>](http://www.codeproject.com/useritems/raidfile.asp) on the subject.

Using XOR we can find the differences between the original page and the copy of the page. Some vary fast code can XOR the page and it’s backup and rewrite the results to the backup:

    // psuedo-code. A real-world implementation should use SMID
    for (unsigned short j = 0; j < PAGE_SIZE; ++j) {
        const BYTE a = backup[j];
        const BYTE b = page[j];
        backup[j] = (a ^ b);
    }

Any byte that hasn’t changed will come back zero from the XOR operation. Bytes that have changed will be non-zero. That doesn’t look like a space saving except for the fact that pages with sparse changes will have lots of zeros and compress very, very well. In addition, and as Daniel notes, by storing the XOR we can always get to the “other” memory state from the “before” or “after” state – hence, we now can redo what we undo. Sweet!

## RLE: Delta Compression

Once we decide that changes should be kept (see `CommitTransaction`), we can calculate the XOR deltas, compress them, and hold onto them while discarding the backup page. This technique reduces the memory overhead of the system considerably.

To demonstrate the concept of compressing the delta (the XOR of the page and the backup) I implemented a very simple Run Length Encoding (RLE) algorithm. The code simply looks for long runs of duplicate bytes and encodes them as a count and the byte. So, for example, a run of 100 “0”s is compressed down to 2 bytes. Compression on random data is poor, however, and in production you’d want to use something like zlib to get better worst-case performance.

The details of the RLE compression are separated out in *Compress.h* and *Compress.cpp* . If you can provide an implementation that fits into these two files nicely (and is speedy) I’ll add it to this article and give you credit here. It's an interesting problem, since we know that the block to be compressed will always be `PAGE_SIZE` bytes.

## STL Integration, MFC dangers

The designers of STL (bless their hearts) decided to include the ability to control the memory allocation done by containers (list, vector, map, etc.). This is very cool. It allows us to write an allocator that uses our memory manager to put STL containers on transacted pages. Translation: We can do transactions that involve manipulations of STL containers and objects.

See *Allocator.h* for the not-so-gory details of the allocator, and *MemTest.cpp* for a demonstration.

It would be cool to do the same on MFC classes, but that is generally a bad idea. MFC classes often do non-memory based things. Classes derived from `CObject` or `CCommandTarget` could be transacted using this technique, but be careful to avoid holding pointers to non-transacted objects in transacted objects and vise-versa. The pointers could become invalid after an undo or redo.

## The Demo App(s)

There are three demo applications included with this article. The first is a bare-bones console app that tests much of the functionality of the engine. Since it is well commented, I’ll just refer you to the directory *MemTest* rather than include 200+ duplicate lines in this document.

The second demo app, *DrawIt* is more interesting, since it integrates this undo approach with a simple MFC-based application. The application does simple drawing (vector based) of shapes. It processes mouse down, move and up messages and interactively creates random shapes based on the input. Two toolbar commands automate the creation of large numbers of shapes by:

1.  Opening 1000 transactions with each adding a single random shape in a random location.
2.  Opening a single transaction and adding a 1000 random shapes in a random locations.

I did this to show the difference between lots of small transactions and few large transactions. Both cases work very well. The transaction overhead in both cases is small compared to the time to manipulate the lists and render the items.

A perhaps subtle point in the demo is that the code for creating objects is provided in an external DLL (*DrawFunc.dll*) that has zero knowledge of the transaction mechanisms in the host application. That makes it very, very simple for a replacement DLL to be implemented for customization or extensibility purposes. It's worth looking at the subproject, and the sketch object in particular, to note just how simple life can be for add-in providers.

Another interesting aspect of the demo application is the long transaction support. You can open a transaction, make lots of changes to the document by adding items interactively or using the abuse commands, and then commit or cancel the changes as one large chunk. If the changes are committed, they will undo and redo as one unit. If the changes are cancelled, the document will return to the previous state (including the intact redo stack) as if none of the changes had happened -- nice, eh?

This second demo application was generated using appwizard. I then added small modifications to `CDrawItApp::InitInstace`, `Run`, `ExitInstance`, `OnUndo` and `OnRedo`. Those modifications are general purpose and generally applicable to MFC apps using Transactions. Some other modifications can be found in *CDrawItView.h*,*.cpp* and *CDrawItDoc.h*, *.cpp*. Those modifications are specific to this application, and you should replace them with your own code.

The third final demo, *DrawItMDI*, demonstrates using the multi-space functionality of Transactions to build an MDI application that maintains individual undo/redo streams for each document. It also implements exception filtering to capture crashes and do reporting.

These demos show the flexibility of the framework, and I hope they will encourage you to try some new ideas yourself. Please recognize that the demo applications make use of code from other projects at CodeProject, and elsewhere. Thanks to Hans Dietrich, Bruce Dawson and Jonathan de Halleux.

## API

There are only a handful of methods in the API, and one of them should be used only once per application. That leaves us with about seven things to remember, which is about the right number.

### SPACEID CreateSpace(size_t initial_size)

Create a transacted heap from which allocations can be requested. A transaction must be opened on the space before it can be used.

### Result Destroy(SPACEID sid)

Destroy a previously created space, freeing all memory associated with it. Keep in mind that destructors will not be called for any objects remaining in the space. Future allocation requests on the space will result in undefined behavior.

### 

### Result DestroyAll()

Destroy all previously created spaces, freeing all memory associated with them. Keep in mind that destructors will not be called for any objects remaining in the spaces. Future allocation requests on the existing spaces will result in undefined behavior.

### Result Clear(SPACEID sid)

Free all memory associated with a space. Keep in mind that destructors will not be called for any objects remaining in the space. Future allocation requests on the space are allowed.

### 

### Result ClearAll()

Free all memory associated with all spaces. Keep in mind that destructors will not be called for any objects remaining in the spaces. Future allocation requests on the spaces are allowed.

### int ExceptionFilter(LPEXCEPTION_POINTERS\* e)

This method provides the major point of integration with the target application’s code. In order to catch memory access violations, you must put a `_try {} _except() {}` block using this exception filter, above all modifications to managed memory (allocated by `Allocate`) in the call stack. The logical place to put the try block is in `main()`, `WinMain()` or around the application’s main message loop.

### Result OpenTransaction(SPACEID sid)

Call this method to open a new transaction. Any open transaction must be closed (committed or cancelled) before another transaction can be started. Outside of a transaction, an attempt to write to protected memory will result in an unhanded exception.

### Result CancelTransaction(SPACEID sid)

Call this method if you’d like to close a transaction without committing any changes. As a result of this call, all changes to memory since the start of the transaction, will be reversed and the transaction will be removed from the undo list. The transaction will not be available for undo.

Transactions on the redo stack will still be available for redo. It’s like it never happened. Imagine trying to do this with a procedural undo framework. Cool, eh?

### Result CommitTransaction(SPACEID sid)

Call this method to commit changes made since the last call to `OpenTransaction` and to add the transaction to the undo list. Changes made during the transaction are preserved. If there are transactions on the redo stack, they will be dumped and any pages they contain will be added to the free list.

### TXNID GetLastTransactionId(SPACEID sid)

This method returns an identifier of the last previously committed transaction. Use this method in conjunction with `Undo`/`Redo` to roll the application state to a specific point in its history. This method should be useful, if you need to wrap MM with a procedural framework, since it uniquely identifies each transaction.

### TXNID GetNextTransactionId(SPACEID sid)

This method returns an identifier of the next transaction in the redo stack. Use this method in conjunction with `Undo`/`Redo` to roll the application state to a specific point in its history. This method should be useful, if you need to wrap MM with a procedural framework, since it uniquely identifies each transaction.

### TXNID GetOpenTransactionId(SPACEID sid)

This method returns an identifier of the currently open transaction. Use this method in to determine if `Undo`/`Redo` are available, or if a transaction is already in progress. This method should be useful, if you need to wrap MM with a procedural framework, since it uniquely identifies each transaction.

### Result Undo(SPACEID sid)

Call this method to reverse the changes made in the last transaction.

### Result Redo(SPACEID sid)

Call this method to re-reverse the changes made in the last undo.

### Result TruncateUndo(SPACEID sid)

Drops all transactions in the Undo stack. This is useful, for example, to avoid allowing the user to undo over document or application initialization.

### Result TruncateRedo(SPACEID sid)

Drops all transactions in the Redo stack. This happens automatically when a Transaction is committed while the Redo stack is not empty (think about it). I can't think of why you'd want to do this at the application level.

### void\* Allocate(size_t size, SPACEID sid)

Allocate `size` bytes of transacted memory in the specified space. All objects that should be transacted must be allocated with this method. To simplify creating C++ objects in transacted memory you might try one of the following:

1.  Get a correctly sized piece of memory with `Allocate`, then use <a href="http://www.google.com/search?hl=en&amp;lr=lang_en&amp;ie=UTF-8&amp;oe=UTF-8&amp;safe=off&amp;q=placement+new" target="_blank"><u>placement new</u></a> to put an instance of your class in that memory. E.g:

        Foo* foo = new(Mm::Allocate(sizeof(Foo), mySpaceId)) Foo();

2.  Override `operator`` ``new`() on the class with an implementation that uses `Allocate` to grab memory. This is method is recommended. E.g.:

        class Foo {
          void* operator new(size_t size) { return Mm::Allocate(size, mySpaceId); }
        };

3.  Create a custom allocation method (see `MyNew` and `MyDelete` in *MemTest.cpp*). Also recommended.

### void\* Allocate(void\* hint, size_t size)

If the appropriate space id is inconvenient to access, a hint can be provided to the allocation API. When a hint is provided, Transactions will attempt to find the space in which the hint address resides. If it is successful, an allocation will be made in that space. If not, allocation will fail. Obviously, using a hint instead of a space id adds some performance overhead.

### void Deallocate(void\* p)

Free the block `p` allocated with `Allocate()`. Since no the space is not indicated in the parameter list, the method needs to check if the address was originally allocated by Transactions, and if so in which space. This obviously makes the method slower, so prefer the below form:

### void Deallocate(void\* p, SPACEID sid)

This is the preferred deallocation method, but beware that no attempt is made to double-check the space id. If it is wrong, the deallocation will simply fail. This is the faster of the three deallocation signatures.

### void Deallocate(void\* p, size_t size)

Mainly used by Mm::Allocator, not much reason to use it otherwise.

### void\* Reallocate(void\* p, size_t size)

Attempts to reallocate the space at p to a new size. If the new size is smaller than the existing allocation it will always work. If the requested size is larger than the existing size, it may (in fact probably will) fail. Don't pass null p since it is needed to determine which space to use.

### void\* Reallocate(void\* p, size_t size, SPACEID sid)

Same ass above, but null p is okay since the space is specified. This is the faster of the two forms.

## Conclusion

I hope that this article has given you some insight into yet another way to do undo/redo. The method presented here has some significant advantages, but can be difficult to understand and debug. Among the advantages are:

- Low memory overhead
- High performance and scalable
- Easy to use

On a final note, and just to twist your mind, consider that this technique is fast enough to allow you to “Peek back in time.” That is, if it is useful to know where an object was, what color it was, or what value it had in a previous transaction, you can easily modify this code to do that. Hmm. That could be useful.

Enjoy!

## Version History

- **UPDATE June 18, 2004**:
  - Added support for multiple, individually transacted "spaces" (aka. heaps)
  - Many bug fixes, ported to VC7.1
  - More readable code
  - MDI Sample Applicationn

Version 1.3 posted Jan. 7, 2003 to CodeProject

Version 1.2 posted Dec. 17, 2002 to CodeProject

- Added commentary based on Tom Morris' tutorial.

Version 1.1 posted Oct. 7, 2002 to CodeProject

- New API method `Mm::Clear()` dumps all VM and resets undo and redo stack
- New demo DrawIt added to show MFC integration.
- Removed reference to Result.h that caused build problems.

Version 1.0 posted Oct. 4, 2002 to CodeProject

</div>

<div>

</div>

## License

<div>

This article has no explicit license attached to it but may contain usage terms in the article text or the download files themselves. If in doubt please contact the author via the discussion board below.

A list of licenses authors might use can be found [<u>here</u>](http://nsclass.spaces.live.com/info/Licenses.aspx)

</div>

## About the Author

<table data-cellspacing="5" data-cellpadding="0" width="100%" data-border="0">
<colgroup>
<col style="width: 50%" />
<col style="width: 50%" />
</colgroup>
<tbody>
<tr data-valign="top">
<td style="width: 155px" data-valign="top"><strong><a href="http://nsclass.spaces.live.com/script/Membership/Profiles.aspx?mid=49251"><u>compiler</u></a></strong>
<p><u></u><br />
<span></span></p></td>
<td>A compiler warns of bogasity, ignore it at your peril. Unless you've done the compiler's job yourself, don't criticize it.
<table>
<tbody>
<tr>
<td>Location:</td>
<td width="100%"><span><img src="http://nsclass.spaces.live.com/script/Geo/Images/US.gif" width="16" height="11" alt="United States" /> United States</span></td>
</tr>
</tbody>
</table></td>
</tr>
</tbody>
</table>

<div style="overflow:hidden;white-space:nowrap;text-align:center;padding:10px;">

</div>
