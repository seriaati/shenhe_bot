# Your account and Shenhe

There are two major ways of linking your Genshin Impact account: UID and Cookie (Using script or email & password)

### 🔢 UID

This is the safest login method, the only thing you are giving to Shenhe is your UID in Genshin Impact, and there's nothing else. However, the commands you can use will be limited, this is why most players move on to the second login method: Cookie.\
Noticeably, with the power of [Enka](https://enka.shinshin.moe/), you get to use many useful features with just your UID.

### 🍪 Cookie

#### What is a Cookie?

When you first login into the Hoyolab website with your account, a text file called "Cookie" is created and stored on your computer.\
Have you ever wondered why the next time you go to the Hoyolab website, you don't need to enter your email and password again?\
It's because your browser uses the Cookie that was stored to identify you as the owner of the Hoyolab account.\
The Cookie is an encrypted string of text that temporarily stores your account's information so that you don't have to log in with your email and password every single time.\
This feature is convenient, but of course, it comes with security issues.\
In other words, anyone that has access to your account's Cookie will be treated as the owner of your account.\
And yes! Shenhe asks you to give her your Cookie because data like Spiral Abyss and real-time notes are only visible to the owner of the Hoyolab account, this is why you can't use these commands without linking your account to a Cookie.

#### Can I hack your account?

NO! Even though I have your Cookie, that doesn't mean I can do anything I want with your account.

1. I can't change your password because that requires confirmation with your email. I have no idea what your email address is, not to mention its password.
2. Two-factor authentication exists, which makes it completely impossible to steal your account if you have it set up.

### ✉️ Email and password

Normally, you obtain your Cookie by typing a javascript in the address bar.\
However, some users struggle with that approach.\
So Shenhe partners with the [Hutao Login Gateway Service](https://github.com/Hu-tao-bot/login-service-library-python) that allows you to obtain your account's Cookie with the method you are familiar with - Email and password.

#### What's going on here?

You enter your email and password -> complete the CAPTCHA test -> the HLGS will send an API request to Hoyoverse with your email and password encrypted -> Hoyoverse responds the request with your account's Cookie\
Neither me and [the author of HLGS](https://github.com/mrwan200) store your Hoyoverse email and password.\
We're just trying to get your account's Cookie, that's all.\
If you don't trust us, DON'T use this method. I personally strongly recommend you to use the script approach.\
Even if we attempt to login to Genshin Impact with your email and password, we still need an email verification from you. I have no idea what your email address is, not to mention its password.

### 🤝 Trust between you and me

I can do the following things, but I swear I won't do them:

1. Create community posts with your Hoyolab account
2. Share your Cookie with other people (But remember, nobody can hack your account with only the Cookie)

### ⛔ Can your account get banned?

1. There have been 0 record of Hoyoverse banning accounts for using their API (with Cookies)
2. Large Genshin Discord bots like Genshin Wizard have millions of users using the same API

### 🛡️ Is your data secure?

Your Cookie is stored in Shenhe's database, which locates on Amazon's AWS server.\
Amazon is a pretty huge company, that's all I can say.

### ⚠️ Use at your own risk

Now that you have been informed of all the things above, it's still up to you to decide whether you want to link your account with Cookie or not.\
I will try my best to keep your account data secure, but I can't guarantee that something unexpected won't happen.\
Remember, I am not responsible for any account-related issues.\
Lastly, you can always remove your account data at any time you want using the /accounts command.\
Additionally, your Cookie will expire/become invalid once you change your account's password.

### 📖 Source Code

Shenhe: [https://github.com/seriaati/shenhe\_bot](https://github.com/seriaati/shenhe\_bot)

Hutao Login Gateway: [https://github.com/Hu-tao-bot/login-service-library-python](https://github.com/Hu-tao-bot/login-service-library-python)
