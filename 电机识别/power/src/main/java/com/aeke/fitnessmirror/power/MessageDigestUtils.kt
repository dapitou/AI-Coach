import java.security.MessageDigest

object MessageDigestUtils {
    fun getSha256(datas: ByteArray): String? {
        try {
            val digest = MessageDigest.getInstance("SHA-256")
            val hashBytes = digest.digest(datas)
            val hexString = StringBuilder()
            for (b in hashBytes) {
                // 将每个字节转换为两位十六进制数
                val hex = Integer.toHexString(0xff and b.toInt())
                // 如果需要，前面补零以确保长度为2
                if (hex.length == 1) {
                    hexString.append('0')
                }
                hexString.append(hex)
            }
            return hexString.toString()
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return null
    }

    fun getMd5(datas: ByteArray): String? {
        try {
            val digest = MessageDigest.getInstance("MD5")
            val hashBytes = digest.digest(datas)
            val hexString = StringBuilder()
            for (b in hashBytes) {
                // 将每个字节转换为两位十六进制数
                val hex = Integer.toHexString(0xff and b.toInt())
                // 如果需要，前面补零以确保长度为2
                if (hex.length == 1) {
                    hexString.append('0')
                }
                hexString.append(hex)
            }
            return hexString.toString()
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return null
    }
}