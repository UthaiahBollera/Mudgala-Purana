const basePath=process.env.MUDGALA_PAGES_PREVIEW==='1'?'/sanskrit-kannada':'';
export default {basePath,env:{NEXT_PUBLIC_MUDGALA_BASE_PATH:basePath},output:'export',trailingSlash:true,images:{unoptimized:true},poweredByHeader:false};
