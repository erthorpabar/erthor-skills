package main

import (
	"fmt"
	"time"

	"github.com/spf13/viper"

	"github.com/gin-gonic/gin"

	"gorm.io/driver/mysql"
	"gorm.io/gorm"
)

// ——————————————————sql————————————————————
/*
	左边 = 代码中的名称
	中间 = 数据类型
	右边 = 会自动映射 如 UserId -> user_id 所以在 column 后 指定数据库中列的名称
*/
type U struct {
	Id         int       `gorm:"primaryKey;column:id"`
	Name       string    `gorm:"column:name"`
	Password   string    `gorm:"column:password"`
	CreateTime time.Time `gorm:"column:create_time;autoCreateTime"`
	UpdateTime time.Time `gorm:"column:update_time;autoUpdateTime"`
}

// 结构体 -> 数据表的名称
func (U) TableName() string {
	return "user"
}

// ————————————————————————————————————————————
func Hello(c *gin.Context) {
	c.JSON(200, gin.H{"message": "Hello, World!"})
}

func main() { // 唯一程序入口 内部不允许定义函数
	// ————————————————环境变量————————————————————
	v := viper.New()                 // 初始化viper
	v.SetConfigFile("./config.yaml") // 配置文件路径
	v.AutomaticEnv()                 // 可通过 命令行 让程序可以读取优先级更高的系统环境变量
	v.ReadInConfig()                 // 读取环境变量
	// // 打印
	fmt.Println(v.GetString("LLM_URL"))
	fmt.Println(v.GetString("LLM_API_KEY"))
	fmt.Println(v.GetString("LLM_MODEL"))

	// ————————————————初始化————————————————————
	gin.SetMode(gin.ReleaseMode) // gin线上发布模式
	engine := gin.Default()      // 创建一个gin引擎

	// ————————————————全局中间件—————————————————————
	engine.Use(gin.Logger())   // 记录请求日志
	engine.Use(gin.Recovery()) // 恢复请求

	// ————————————————定义路由————————————————————
	// get
	engine.GET("/", Hello)

	// post
	engine.POST("/", Hello)

	// 组路由
	{
		g1 := engine.Group("/v1") // 直接默认增加在路由中
		g1.GET("/", Hello)
	}

	// 数据验证
	type User struct {
		Name string `json:"name" binding:"required" default:"美羊羊"`
		Age  int    `json:"age" binding:"required" default:"20"`
	}
	engine.POST("/user", func(c *gin.Context) {
		var data User
		if err := c.ShouldBindJSON(&data); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}
		c.JSON(200, gin.H{"name": data.Name, "age": data.Age})
	})

	// ————————————————mysql——————————————————
	// 创建连接
	host := "localhost"
	port := 3306
	database := "test"
	username := "root"
	password := "1234"
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?charset=utf8mb4&parseTime=True&loc=Local", username, password, host, port, database)
	db, err := gorm.Open(mysql.Open(dsn), nil)
	if err != nil { // 如果连接失败
		panic("failed to connect database") // 退出程序
	}

	// 连接池
	sqlDB, _ := db.DB()
	sqlDB.SetMaxIdleConns(10)           // 最大空闲连接数
	sqlDB.SetMaxOpenConns(100)          // 最大连接数
	sqlDB.SetConnMaxLifetime(time.Hour) // 空闲超时自动关闭连接

	{
		gsql := engine.Group("/sql") // 直接默认增加在路由中
		// 写入数据
		// db.Exec("insert into user (name, password) values (?, ?)", "123", "123456")
		gsql.POST("/create", func(c *gin.Context) {
			var data U
			if err := c.ShouldBindJSON(&data); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			db.Create(&U{Name: data.Name, Password: data.Password})
			c.JSON(200, gin.H{"status": "success"})
		})

		// 读取数据(查询全部数据)
		// db.Raw("select * from user").Scan(&instance2)
		gsql.POST("/find", func(c *gin.Context) {
			var data []U // 修复：使用切片查询所有数据
			db.Find(&data)
			c.JSON(200, gin.H{"data": data})
		})

		// 修改数据
		// db.Model(&User{}).Where("id = ?", 4).Updates(map[string]any{"name": "777", "password": "78945324234236"})
		gsql.POST("/update", func(c *gin.Context) {
			var data U
			if err := c.ShouldBindJSON(&data); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			db.Model(&U{}).Where("id = ?", data.Id).Updates(map[string]any{"name": data.Name, "password": data.Password})
			c.JSON(200, gin.H{"status": "success"})
		})

		// 删除数据
		// db.Delete(&User{}).Where("id = ?", 4)
		gsql.POST("/delete", func(c *gin.Context) {
			var data U
			if err := c.ShouldBindJSON(&data); err != nil {
				c.JSON(400, gin.H{"error": err.Error()})
				return
			}
			db.Where("id = ?", data.Id).Delete(&U{}) // 修复：正确的删除语法
			c.JSON(200, gin.H{"status": "success"})
		})
	}

	// ————————————————启动服务————————————————————
	engine.Run("127.0.0.1:7004")

}

// 初始化 go mod init aaa

/* 下载依赖

环境变量 viper
go get github.com/spf13/viper

后端框架 gin
go get github.com/gin-gonic/gin

orm框架 gorm
go get gorm.io/gorm

mysql驱动
go get gorm.io/driver/mysql

websocket
go get github.com/gorilla/websocket

*/

// 运行 自动寻找main 作为唯一程序入口
// go run a.go
// go run . --port 5678
